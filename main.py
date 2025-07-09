#!/usr/bin/env python3
"""
SpotEye Apartment Monitoring System - Main Application
A monitoring system for W|27 German student apartments
"""

import logging
import sys
import time
from datetime import datetime

from config import get_config
from scraper import ApartmentScraper
from storage import ApartmentStorage
from notification import EmailNotifier


class SpotEyeMonitor:
    """Main application class that coordinates all monitoring components"""
    
    def __init__(self):
        """Initialize the monitoring system"""
        self.config = get_config()
        self.setup_logging()
        
        # Initialize components
        self.scraper = ApartmentScraper(self.config, self.logger)
        self.storage = ApartmentStorage(self.config, self.logger)
        self.notifier = EmailNotifier(self.config, self.logger)
        
        self.logger.info("SpotEye monitoring system initialized")
    
    def setup_logging(self):
        """Configure logging for the application"""
        log_level = getattr(logging, self.config['logging']['level'])
        log_format = self.config['logging']['format']
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.config['logging']['file'], encoding='utf-8')
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging system initialized")

    def run_once(self):
        """Execute monitoring once"""
        self.logger.info("Starting monitoring execution...")
        
        try:
            # 1. Scrape current data
            current_apartments = self.scraper.scrape_apartments()
            self.logger.info(f"Retrieved {len(current_apartments)} apartment listings")
            
            # 2. Load historical data
            historical_data = self.storage.load_historical_data()
            
            # 3. Detect changes
            changes = self.storage.detect_changes(current_apartments, historical_data)
            
            # 4. Send notifications
            if changes:
                self.logger.info(f"Found {len(changes)} changes")
                self.notifier.send_notification(changes)
            else:
                self.logger.info("No changes found")
            
            # 5. Save current data
            updated_data = self.storage.create_updated_data(current_apartments)
            self.storage.save_data(updated_data)
            
            # 6. Log statistics
            stats = self.storage.get_statistics(current_apartments)
            self.logger.info(f"Monitoring complete - Total: {stats['total']}, "
                           f"Available: {stats['by_status'].get('available', 0)}, "
                           f"Soon: {stats['by_status'].get('soon', 0)}")
            
        except Exception as e:
            self.logger.error(f"Monitoring execution failed: {e}")
            raise

    def run_continuous(self):
        """Run monitoring continuously with configured intervals"""
        interval = self.config['monitoring']['check_interval']
        self.logger.info(f"Starting continuous monitoring with {interval} minute intervals")
        
        while True:
            try:
                self.run_once()
                
                # Wait for next check
                self.logger.info(f"Waiting {interval} minutes until next check...")
                time.sleep(interval * 60)  # Convert minutes to seconds
                
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous monitoring: {e}")
                self.logger.info(f"Retrying in {interval} minutes...")
                time.sleep(interval * 60)

    def test_email(self):
        """Test email notification system"""
        self.logger.info("Testing email notification system...")
        
        try:
            success = self.notifier.send_test_notification()
            if success:
                print("✅ Email test successful! Check your inbox.")
            else:
                print("❌ Email test failed. Check your configuration.")
            return success
            
        except Exception as e:
            self.logger.error(f"Email test failed: {e}")
            print(f"❌ Email test failed: {e}")
            return False

    def show_status(self):
        """Show current system status"""
        print("=== SpotEye System Status ===")
        
        try:
            # Load current data
            historical_data = self.storage.load_historical_data()
            apartments = historical_data.get('apartments', [])
            
            if apartments:
                stats = self.storage.get_statistics(apartments)
                last_check = historical_data.get('last_check', 'Never')
                
                print(f"Last Check: {last_check}")
                print(f"Total Apartments: {stats['total']}")
                print("\nAvailability Status:")
                for status, count in stats['by_status'].items():
                    print(f"  {status.title()}: {count}")
                
                print("\nApartment Types:")
                for apt_type, count in stats['by_type'].items():
                    print(f"  {apt_type}: {count}")
                
                if stats['price_stats']:
                    print(f"\nPrice Range: €{stats['price_stats']['min']} - €{stats['price_stats']['max']}")
                    print(f"Average Price: €{stats['price_stats']['avg']}")
            else:
                print("No apartment data available yet.")
                
        except Exception as e:
            print(f"Error displaying status: {e}")


def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SpotEye Apartment Monitoring System')
    parser.add_argument('--once', action='store_true', help='Run monitoring once and exit')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--test-email', action='store_true', help='Test email notification')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    print("=== SpotEye Apartment Monitoring System ===")
    print("Initializing...")
    
    try:
        monitor = SpotEyeMonitor()
        
        if args.test_email:
            monitor.test_email()
        elif args.status:
            monitor.show_status()
        elif args.once:
            monitor.run_once()
            print("Single monitoring run completed!")
        elif args.continuous:
            monitor.run_continuous()
        else:
            # Default: show help and run once
            parser.print_help()
            print("\nRunning once by default...")
            monitor.run_once()
            print("Monitoring completed!")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 