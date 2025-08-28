#!/usr/bin/env python3
"""Test the 5_min data integration"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.stock_data import (
    get_available_stocks,
    load_daily_stock_data,
    load_intraday_stock_data,
    get_stock_data_for_date
)

def test_5min_integration():
    print("Testing 5_min Data Integration")
    print("=" * 50)
    
    # Test available symbols
    symbols = get_available_stocks()
    print(f"Available symbols: {len(symbols)} - {symbols}")
    
    # Test NVDA data for today (should come from 5_min aggregation)
    print(f"\nTesting NVDA data for today (2025-08-25)...")
    result = get_stock_data_for_date("NVDA", "2025-08-25")
    
    if result['daily']:
        daily = result['daily']
        print(f"Daily data found: {daily.get('source', 'unknown source')}")
        print(f"  Date: {daily['date']}")
        print(f"  Open: {daily['open']:.2f}")
        print(f"  High: {daily['high']:.2f}")
        print(f"  Low: {daily['low']:.2f}")
        print(f"  Close: {daily['close']:.2f}")
        print(f"  Volume: {daily['volume']:,}")
    else:
        print("No daily data found!")
    
    print(f"Intraday records: {len(result['intraday'])}")
    if result['intraday']:
        latest = result['intraday'][0]
        print(f"  Latest: {latest['datetime']} - Close: {latest['close']:.2f}")
    
    # Test another symbol with 5_min data
    print(f"\nTesting MRVL data for today...")
    mrvl_result = get_stock_data_for_date("MRVL", "2025-08-25")
    
    if mrvl_result['daily']:
        daily = mrvl_result['daily']
        print(f"MRVL daily data: {daily.get('source', 'unknown source')}")
        print(f"  Close: {daily['close']:.2f}, Volume: {daily['volume']:,}")
    
    # Test comprehensive daily data loading
    print(f"\nTesting comprehensive daily data for NVDA...")
    all_daily = load_daily_stock_data("NVDA")
    print(f"Total daily records: {len(all_daily)}")
    
    # Count data sources
    sources = {}
    for record in all_daily:
        source = record.get('source', 'legacy')
        sources[source] = sources.get(source, 0) + 1
    
    print("Data source breakdown:")
    for source, count in sources.items():
        print(f"  {source}: {count} records")
    
    print("\n5_min Integration Test Complete!")

if __name__ == "__main__":
    test_5min_integration()
