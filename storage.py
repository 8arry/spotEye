#!/usr/bin/env python3
"""
SpotEye Data Storage Module
Handles apartment data storage, loading, and change detection
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List


class ApartmentStorage:
    """Data storage and change detection for apartment information"""
    
    def __init__(self, config: Dict, logger: logging.Logger):
        """Initialize storage with configuration and logger"""
        self.config = config
        self.logger = logger
        self.data_file = config['data_storage']['file_path']

    def load_historical_data(self) -> Dict:
        """Load historical data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"Loaded historical data with {len(data.get('apartments', []))} apartments")
                    return data
            else:
                self.logger.info("No historical data file found, starting fresh")
                return {'apartments': [], 'last_check': None}
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")
            return {'apartments': [], 'last_check': None}
    
    def save_data(self, data: Dict):
        """Save data to file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(data.get('apartments', []))} apartments to {self.data_file}")
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
    
    def detect_changes(self, current_data: List[Dict], historical_data: Dict) -> List[Dict]:
        """Detect changes between current and historical data"""
        historical_apartments = historical_data.get('apartments', [])
        
        # Create dictionaries for easy lookup
        historical_dict = {apt.get('id'): apt for apt in historical_apartments if apt.get('id')}
        current_dict = {apt.get('id'): apt for apt in current_data if apt.get('id')}
        
        new_apartments = []
        changed_apartments = []
        
        for apt_id, current_apt in current_dict.items():
            if apt_id not in historical_dict:
                # Only treat as "new" if it's actually interesting (available/soon)
                # Skip if it's just a "taken" apartment on first run
                if current_apt.get('availability') in ['available', 'soon'] or len(historical_apartments) > 0:
                    new_apartments.append({
                        'type': 'new',
                        'apartment': current_apt
                    })
                    self.logger.info(f"New apartment found: {apt_id}")
                else:
                    self.logger.debug(f"Skipping taken apartment on initial load: {apt_id}")
                
            else:
                # Check if availability status changed
                historical_apt = historical_dict[apt_id]
                historical_status = historical_apt.get('availability')
                current_status = current_apt.get('availability')
                
                if historical_status != current_status:
                    # Status changed
                    if current_status in ['soon', 'available'] and historical_status == 'taken':
                        # Changed from taken to available - this is important!
                        changed_apartments.append({
                            'type': 'status_change',
                            'apartment': current_apt,
                            'old_status': historical_status,
                            'new_status': current_status
                        })
                        self.logger.info(f"Status change: {apt_id} from {historical_status} to {current_status}")
                    
                # Check if available date changed
                historical_date = historical_apt.get('available_date')
                current_date = current_apt.get('available_date')
                
                if historical_date != current_date and current_date:
                    changed_apartments.append({
                        'type': 'date_change',
                        'apartment': current_apt,
                        'old_date': historical_date,
                        'new_date': current_date
                    })
                    self.logger.info(f"Date change: {apt_id} from {historical_date} to {current_date}")
        
        all_changes = new_apartments + changed_apartments
        
        if all_changes:
            self.logger.info(f"Found {len(new_apartments)} new apartments and {len(changed_apartments)} changes")
        else:
            self.logger.info("No new apartments or changes detected")
            
        return all_changes

    def create_updated_data(self, current_apartments: List[Dict]) -> Dict:
        """Create updated data structure for saving"""
        return {
            'last_check': datetime.now().isoformat(),
            'apartments': current_apartments,
            'total_apartments': len(current_apartments),
            'last_update': datetime.now().isoformat()
        }

    def get_statistics(self, apartments: List[Dict]) -> Dict:
        """Generate statistics about apartment data"""
        if not apartments:
            return {
                'total': 0,
                'by_status': {},
                'by_type': {},
                'by_location': {},
                'price_stats': {}
            }
        
        stats = {
            'total': len(apartments),
            'by_status': {},
            'by_type': {},
            'by_location': {},
            'price_stats': {}
        }
        
        # Count by status
        for apt in apartments:
            status = apt.get('availability', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # Count by type
        for apt in apartments:
            apt_type = apt.get('type', 'unknown')
            stats['by_type'][apt_type] = stats['by_type'].get(apt_type, 0) + 1
        
        # Count by location
        for apt in apartments:
            location = apt.get('location', 'unknown')
            stats['by_location'][location] = stats['by_location'].get(location, 0) + 1
        
        # Price statistics
        prices = [apt.get('price') for apt in apartments if apt.get('price')]
        if prices:
            stats['price_stats'] = {
                'min': min(prices),
                'max': max(prices),
                'avg': round(sum(prices) / len(prices), 2),
                'count': len(prices)
            }
        
        return stats 