"""
Quick script to query and display data from Orange Box RDS database
Supports multi-device filtering

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.database_service import DatabaseService
import argparse

# Parse arguments
parser = argparse.ArgumentParser(description='Query Orange Box Database')
parser.add_argument('--device', type=str, default=None, 
                   help='Filter by device ID (default: show all devices)')
parser.add_argument('--list-devices', action='store_true',
                   help='List all devices in database')
args = parser.parse_args()

# RDS credentials
db = DatabaseService(
    host='orangebox.csxenzvznekp.ap-southeast-3.rds.amazonaws.com',
    user='orangeboxmaster',
    password='wpiGf0AtihhN2D3AjXUaSl',
    database='orangebox',
    port=3306
)

# List devices if requested
if args.list_devices:
    print("="*80)
    print("ORANGE BOX DATABASE - DEVICE LIST")
    print("="*80)
    devices = db.get_all_devices()
    if devices:
        print(f"\nFound {len(devices)} device(s):\n")
        for i, device in enumerate(devices, 1):
            print(f"{i}. Device ID: {device['device_id']}")
            print(f"   Records: {device['record_count']}")
            print(f"   First seen: {device['first_seen']}")
            print(f"   Last seen: {device['last_seen']}")
            print()
    else:
        print("\nNo devices found in database.")
    sys.exit(0)

print("="*80)
if args.device:
    print(f"ORANGE BOX DATABASE - DATA FOR DEVICE: {args.device}")
else:
    print("ORANGE BOX DATABASE - ALL DEVICES DATA SUMMARY")
print("="*80)

# Today's summary
print("\n1. TODAY'S SESSION SUMMARY:")
print("-"*80)
if args.device:
    summary = db.get_today_summary_by_device(args.device)
else:
    summary = db.get_today_summary()
    
if summary:
    print(f"   Session Start    : {summary['session_start']}")
    print(f"   Session End      : {summary['session_end']}")
    print(f"   Device ID        : {summary['device_id']}")
    print(f"   Total Sorted     : {summary['total_sorted']}")
    print(f"   Organic Count    : {summary['organic_count']}")
    print(f"   Anorganic Count  : {summary['anorganic_count']}")
    print(f"   Location         : ({summary['latitude']}, {summary['longitude']})")
else:
    print("   No data for today")

# Total stats
print("\n2. ALL-TIME STATISTICS (FROM ANALYSIS RESULTS):")
print("-"*80)
if args.device:
    stats = db.get_stats_by_device(args.device)
else:
    stats = db.get_total_stats()
    
if stats:
    print(f"   Total Records    : {stats.get('total_records', 0)}")
    print(f"   Organic Count    : {stats.get('organic_count', 0)}")
    print(f"   Anorganic Count  : {stats.get('anorganic_count', 0)}")
    print(f"   Average Confidence : {stats.get('avg_confidence', 0):.2%}")
    if args.device:
        print(f"   Device ID        : {args.device}")
else:
    print("   No data available")

# Recent analysis results
print("\n3. RECENT ANALYSIS RESULTS (Last 10):")
print("-"*80)
records = db.get_recent_analysis(limit=10)
if records:
    print(f"   {'#':>2} | {'Timestamp':<19} | {'Label':>10} | {'Conf':>6} | {'Bin':>7} | {'Angle':>5} | {'Location':<20}")
    print("   " + "-"*76)
    for i, rec in enumerate(records, 1):
        loc_str = f"({rec['latitude']:.4f},{rec['longitude']:.4f})" if rec['latitude'] else "(no loc)"
        print(f"   {i:2d} | {str(rec['timestamp']):<19} | {rec['label']:>10} | "
              f"{rec['confidence']:>6.2%} | {rec['bin_assignment']:>7} | {rec['bin_angle']:>5}° | {loc_str:<20}")
else:
    print("   No records found")

# Recent locations
print("\n4. RECENT GPS LOCATIONS (Last 10):")
print("-"*80)
locations = db.get_recent_locations(limit=10)
if locations:
    print(f"   {'#':>2} | {'Timestamp':<19} | {'Latitude':>12} | {'Longitude':>12} | {'Accuracy':>8} | {'Source':>6}")
    print("   " + "-"*76)
    for i, loc in enumerate(locations, 1):
        print(f"   {i:2d} | {str(loc['timestamp']):<19} | {loc['latitude']:>12.6f} | "
              f"{loc['longitude']:>12.6f} | {loc['accuracy']:>8.2f}m | {loc['source']:>6}")
else:
    print("   No locations found")

print("\n" + "="*80)
print("Query completed successfully!")
print("="*80)
