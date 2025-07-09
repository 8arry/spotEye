#!/usr/bin/env python3
"""
Simple data viewer for SpotEye apartment data
"""

import json
import os
from datetime import datetime


def view_current_data():
    """Display current apartment data in detail"""
    data_file = 'apartment_data.json'
    
    if not os.path.exists(data_file):
        print("❌ No data file found. Run monitoring first.")
        return
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        apartments = data.get('apartments', [])
        last_check = data.get('last_check', 'Unknown')
        
        print("=" * 60)
        print("🏠 SPOTEYE APARTMENT DATA")
        print("=" * 60)
        print(f"📅 Last Check: {last_check}")
        print(f"📊 Total Apartments: {len(apartments)}")
        print()
        
        if not apartments:
            print("❌ No apartment data available.")
            return
        
        # Group by availability status
        by_status = {}
        for apt in apartments:
            status = apt.get('availability', 'unknown')
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(apt)
        
        # Display by status
        for status, apt_list in by_status.items():
            print(f"📋 {status.upper()} ({len(apt_list)} apartments)")
            print("-" * 40)
            
            for apt in apt_list:
                apt_id = apt.get('id', 'N/A')
                apt_type = apt.get('type', 'N/A')
                balcony = apt.get('balcony', 'N/A')
                location = apt.get('location', 'N/A')
                size = apt.get('size', 'N/A')
                price = apt.get('price', 'N/A')
                available_date = apt.get('available_date', None)
                barrier_free = apt.get('barrier_free', False)
                
                print(f"🏠 Apartment {apt_id}")
                print(f"   Type: {apt_type}, Balcony: {balcony}")
                print(f"   Location: {location}")
                print(f"   Size: {size}㎡, Price: €{price}")
                
                if available_date:
                    print(f"   📅 Available from: {available_date}")
                
                if barrier_free:
                    print(f"   ♿ Barrier-free accessible")
                
                print()
        
        # Summary statistics
        print("📊 SUMMARY")
        print("-" * 20)
        for status, count in [(s, len(by_status.get(s, []))) for s in ['available', 'soon', 'taken']]:
            if count > 0:
                print(f"   {status.title()}: {count}")
        
        # Price statistics
        prices = [apt.get('price') for apt in apartments if apt.get('price')]
        if prices:
            print(f"   Price range: €{min(prices)} - €{max(prices)}")
            print(f"   Average: €{sum(prices)/len(prices):.2f}")
        
    except Exception as e:
        print(f"❌ Error reading data: {e}")


if __name__ == "__main__":
    view_current_data() 