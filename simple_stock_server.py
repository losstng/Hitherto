#!/usr/bin/env python3
"""Simple FastAPI server for testing the stock endpoints."""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the PYTHONPATH environment variable as well
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

# Import stock data functions directly
from backend.services.stock_data import (
    get_available_stocks,
    load_daily_stock_data,
    load_intraday_stock_data,
    get_stock_data_for_date
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Stock Data API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "Stock Data API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/stocks/symbols")
def get_available_symbols():
    """Get list of available stock symbols from CSV files."""
    logger.info("Fetching available stock symbols")
    try:
        symbols = get_available_stocks()
        logger.info(f"Found {len(symbols)} symbols")
        return {"success": True, "data": symbols, "error": None}
    except Exception as e:
        logger.exception("Failed to fetch available symbols")
        return {"success": False, "data": None, "error": str(e)}

@app.get("/stocks/daily/{symbol}")
def get_daily_data(symbol: str, start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None)):
    """Get daily OHLCV data for a symbol."""
    logger.info(f"Fetching daily data for {symbol}")
    try:
        data = load_daily_stock_data(symbol, start_date, end_date)
        logger.info(f"Returning {len(data)} daily records for {symbol}")
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        logger.exception(f"Failed to fetch daily data for {symbol}")
        return {"success": False, "data": None, "error": str(e)}

@app.get("/stocks/data/{symbol}/{date}")
def get_stock_data_by_date(symbol: str, date: str):
    """Get both daily and intraday data for a symbol on a specific date."""
    logger.info(f"Fetching stock data for {symbol} on {date}")
    try:
        data = get_stock_data_for_date(symbol, date)
        logger.info(f"Returning data for {symbol} on {date}: daily={data.get('daily') is not None}, intraday={len(data.get('intraday', []))}")
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        logger.exception(f"Failed to fetch stock data for {symbol} on {date}")
        return {"success": False, "data": None, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting simple stock API server...")
    uvicorn.run(
        "simple_stock_server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
