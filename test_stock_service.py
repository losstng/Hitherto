#!/usr/bin/env python3
"""Test script to verify the stock data service works correctly."""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.stock_data import (
    get_available_stocks,
    load_daily_stock_data,
    load_intraday_stock_data,
    get_stock_data_for_date
)

def test_available_stocks():
    """Test getting available stock symbols."""
    print("Testing get_available_stocks()...")
    symbols = get_available_stocks()
    print(f"Found {len(symbols)} symbols: {symbols}")
    return symbols

def test_daily_data(symbol="NVDA"):
    """Test loading daily data for a symbol."""
    print(f"\nTesting load_daily_stock_data('{symbol}')...")
    try:
        data = load_daily_stock_data(symbol)
        print(f"Loaded {len(data)} daily records for {symbol}")
        if data:
            print(f"First record: {data[0]}")
            print(f"Last record: {data[-1]}")
        return data
    except Exception as e:
        print(f"Error loading daily data: {e}")
        return []

def test_stock_data_for_date(symbol="NVDA", date="2025-07-01"):
    """Test getting stock data for a specific date."""
    print(f"\nTesting get_stock_data_for_date('{symbol}', '{date}')...")
    try:
        data = get_stock_data_for_date(symbol, date)
        print(f"Result for {symbol} on {date}:")
        print(f"  Daily data: {data.get('daily')}")
        print(f"  Intraday records: {len(data.get('intraday', []))}")
        return data
    except Exception as e:
        print(f"Error getting stock data for date: {e}")
        return {}

if __name__ == "__main__":
    print("Testing Stock Data Service\n" + "="*40)
    
    # Test 1: Get available symbols
    symbols = test_available_stocks()
    
    # Test 2: Load daily data
    if "NVDA" in symbols:
        daily_data = test_daily_data("NVDA")
    
    # Test 2b: Load daily data for MRVL to test combined sources
    if "MRVL" in symbols:
        mrvl_data = test_daily_data("MRVL")
    
    # Test 3: Get data for specific date
    if "NVDA" in symbols:
        date_data = test_stock_data_for_date("NVDA", "2025-07-01")
    
    # Test 4: Get data for a recent date (should have intraday data)
    if "NVDA" in symbols:
        recent_data = test_stock_data_for_date("NVDA", "2025-08-13")
    
    # Test 5: Check what date ranges we have
    if "NVDA" in symbols:
        print(f"\nTesting date ranges...")
        intraday_data = load_intraday_stock_data("NVDA")
        if intraday_data:
            print(f"Intraday data: {len(intraday_data)} records")
            print(f"  First: {intraday_data[0]['date']} {intraday_data[0]['time']}")
            print(f"  Last: {intraday_data[-1]['date']} {intraday_data[-1]['time']}")
    
    print("\nTests completed!")
