"""
Service for loading and processing stock data from CSV files.
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

# Path to raw data directory - assume we're in backend/services, so go up two levels
RAW_DATA_DIR = Path(__file__).parent.parent.parent / "raw_data"
DAILY_DATA_DIR = RAW_DATA_DIR
INTRADAY_DATA_DIR = RAW_DATA_DIR / "5_min"
INTRADAY_FOLDER = RAW_DATA_DIR / "intraday"

def _aggregate_daily_from_5min(symbol: str) -> List[Dict[str, Any]]:
    """Aggregate daily OHLCV data from 5-minute data."""
    try:
        five_min_file = INTRADAY_DATA_DIR / f"{symbol}.csv"
        if not five_min_file.exists():
            return []
        
        df = pd.read_csv(five_min_file)
        
        # Convert datetime column
        df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True)
        df['date'] = df['Datetime'].dt.date
        
        # Group by date and aggregate OHLCV
        daily_agg = df.groupby('date').agg({
            'Open': 'first',   # First opening price of the day
            'High': 'max',     # Highest price of the day
            'Low': 'min',      # Lowest price of the day
            'Close': 'last',   # Last closing price of the day
            'Volume': 'sum',   # Total volume for the day
            'Datetime': 'first'  # First datetime for reference
        }).reset_index()
        
        # Convert to standardized format
        result = []
        for _, row in daily_agg.iterrows():
            result.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'datetime': row['Datetime'].isoformat(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']),
                'source': '5_min_aggregated'
            })
        
        logger.debug(f"Aggregated {len(result)} daily records from 5_min data for {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error aggregating 5_min data for {symbol}: {e}")
        return []

def get_available_stocks() -> List[str]:
    """Get list of available stock symbols from CSV files."""
    try:
        stocks = set()
        
        # Check daily_ prefixed files
        daily_files = list(DAILY_DATA_DIR.glob("daily_*.csv"))
        for file in daily_files:
            symbol = file.stem.replace("daily_", "")
            stocks.add(symbol)
        
        # Check root level CSV files (but not daily_ prefixed ones)
        root_files = list(DAILY_DATA_DIR.glob("*.csv"))
        for file in root_files:
            if not file.stem.startswith("daily_"):
                stocks.add(file.stem)
        
        # Check 5_min data
        intraday_files = list(INTRADAY_DATA_DIR.glob("*.csv"))
        for file in intraday_files:
            if file.stem not in [".gitkeep", "volume_alerts"]:
                stocks.add(file.stem)
        
        # Check intraday folder
        intraday_folder_files = list(INTRADAY_FOLDER.glob("intraday_*.csv"))
        for file in intraday_folder_files:
            symbol = file.stem.replace("intraday_", "")
            stocks.add(symbol)
        
        return sorted(list(stocks))
    except Exception as e:
        logger.error(f"Error getting available stocks: {e}")
        return []

def load_daily_stock_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load daily OHLCV data for a symbol from all available sources."""
    try:
        all_data = []
        
        # Try daily_ prefixed file first
        daily_file = DAILY_DATA_DIR / f"daily_{symbol}.csv"
        if daily_file.exists():
            df = pd.read_csv(daily_file)
            all_data.extend(_process_daily_dataframe(df, symbol, "daily_ file"))
        
        # Try root level file
        root_file = DAILY_DATA_DIR / f"{symbol}.csv"
        if root_file.exists():
            df = pd.read_csv(root_file)
            all_data.extend(_process_daily_dataframe(df, symbol, "root file"))
        
        # Always aggregate from 5_min data to get the most recent data
        five_min_daily = _aggregate_daily_from_5min(symbol)
        all_data.extend(five_min_daily)
        
        if not all_data:
            logger.warning(f"No data found for {symbol}")
            return []
        
        # Remove duplicates by date and sort (prioritize source order: daily_ > root > 5_min)
        seen_dates = set()
        unique_data = []
        for record in all_data:
            if record['date'] not in seen_dates:
                unique_data.append(record)
                seen_dates.add(record['date'])
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered_data = []
            for record in unique_data:
                record_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
                
                if start_date:
                    start_dt = pd.to_datetime(start_date).date()
                    if record_date < start_dt:
                        continue
                
                if end_date:
                    end_dt = pd.to_datetime(end_date).date()
                    if record_date > end_dt:
                        continue
                
                filtered_data.append(record)
            unique_data = filtered_data
        
        # Sort by date (most recent first)
        unique_data.sort(key=lambda x: x['date'], reverse=True)
        
        logger.debug(f"Loaded {len(unique_data)} daily records for {symbol}")
        return unique_data
        
    except Exception as e:
        logger.error(f"Error loading daily data for {symbol}: {e}")
        return []

def _process_daily_dataframe(df: pd.DataFrame, symbol: str, source: str) -> List[Dict[str, Any]]:
    """Process a daily data dataframe into standardized format."""
    try:
        # Handle different date column formats
        date_col = None
        if 'Date' in df.columns:
            date_col = 'Date'
        elif 'Datetime' in df.columns:
            date_col = 'Datetime'
        else:
            logger.error(f"No Date or Datetime column found in {symbol} {source}")
            return []
        
        # Convert date column to datetime
        df[date_col] = pd.to_datetime(df[date_col], utc=True)
        
        # Handle volume column format (might have commas)
        if 'Volume' in df.columns:
            df['Volume'] = df['Volume'].astype(str).str.replace(',', '').str.replace('"', '')
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0)
        
        # Handle price columns format (might have quotes)
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('"', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert to list of dicts
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": row[date_col].strftime("%Y-%m-%d"),
                "datetime": row[date_col].isoformat(),
                "open": float(row["Open"]) if pd.notna(row["Open"]) else 0.0,
                "high": float(row["High"]) if pd.notna(row["High"]) else 0.0,
                "low": float(row["Low"]) if pd.notna(row["Low"]) else 0.0,
                "close": float(row["Close"]) if pd.notna(row["Close"]) else 0.0,
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0
            })
        
        logger.debug(f"Processed {len(result)} records from {symbol} {source}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing {symbol} {source}: {e}")
        return []

def load_intraday_stock_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load intraday data for a symbol, prioritizing 5_min data."""
    try:
        df = None
        
        # Try 5_min data first (most current and constantly updated)
        intraday_file = INTRADAY_DATA_DIR / f"{symbol}.csv"
        if intraday_file.exists():
            df = pd.read_csv(intraday_file)
            logger.debug(f"Loaded 5-min data from {intraday_file}")
        else:
            # Fallback to intraday folder (1-minute data)
            intraday_folder_file = INTRADAY_FOLDER / f"intraday_{symbol}.csv"
            if intraday_folder_file.exists():
                df = pd.read_csv(intraday_folder_file)
                logger.debug(f"Loaded 1-min data from {intraday_folder_file}")
        
        if df is None:
            logger.warning(f"No intraday data file found for {symbol}")
            return []
        
        # Convert datetime column
        datetime_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
        df[datetime_col] = pd.to_datetime(df[datetime_col], utc=True)
        
        # Filter by date range if provided
        if start_date:
            start_dt = pd.to_datetime(start_date, utc=True)
            df = df[df[datetime_col].dt.date >= start_dt.date()]
        
        if end_date:
            end_dt = pd.to_datetime(end_date, utc=True)
            df = df[df[datetime_col].dt.date <= end_dt.date()]
        
        # Sort by datetime (most recent first)
        df = df.sort_values(datetime_col, ascending=False)
        
        # Convert to list of dicts
        result = []
        for _, row in df.iterrows():
            result.append({
                "datetime": row[datetime_col].isoformat(),
                "date": row[datetime_col].strftime("%Y-%m-%d"),
                "time": row[datetime_col].strftime("%H:%M"),
                "open": float(row["Open"]) if pd.notna(row["Open"]) else 0.0,
                "high": float(row["High"]) if pd.notna(row["High"]) else 0.0,
                "low": float(row["Low"]) if pd.notna(row["Low"]) else 0.0,
                "close": float(row["Close"]) if pd.notna(row["Close"]) else 0.0,
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0
            })
        
        logger.debug(f"Loaded {len(result)} intraday records for {symbol}")
        return result
        
    except Exception as e:
        logger.error(f"Error loading intraday data for {symbol}: {e}")
        return []

def get_stock_data_for_date(symbol: str, target_date: str) -> Dict[str, Any]:
    """Get both daily and intraday data for a specific date."""
    try:
        # Get daily data for the specific date (includes 5_min aggregated data)
        daily_data = load_daily_stock_data(symbol, target_date, target_date)
        
        # Get intraday data for the specific date (5_min data)
        intraday_data = load_intraday_stock_data(symbol, target_date, target_date)
        
        return {
            "symbol": symbol,
            "date": target_date,
            "daily": daily_data[0] if daily_data else None,
            "intraday": intraday_data
        }
        
    except Exception as e:
        logger.error(f"Error getting stock data for {symbol} on {target_date}: {e}")
        return {
            "symbol": symbol,
            "date": target_date,
            "daily": None,
            "intraday": []
        }
