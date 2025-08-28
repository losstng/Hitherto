try:
    from fastapi import APIRouter, Query
except Exception:  # pragma: no cover - allow running without FastAPI

    class APIRouter:
        def get(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    def Query(default=None):
        return default


import importlib
import logging

from ..env import STOCK_DEFAULT_TICKERS as DEFAULT_TICKERS
from ..schemas import ApiResponse
from ..services.stock_data import (
    get_available_stocks,
    load_daily_stock_data,
    load_intraday_stock_data,
    get_stock_data_for_date
)

try:  # pragma: no cover - optional dependency
    import yfinance as yf
except Exception:
    yf = importlib.import_module("yfinance") if "yfinance" in globals() else None

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/quotes", response_model=ApiResponse)
def get_stock_quotes(tickers: str | None = Query(None)):
    logger.info("Fetching stock quotes")
    symbols = tickers.split(",") if tickers else DEFAULT_TICKERS
    logger.debug("Symbols requested: %s", symbols)
    quotes = []
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            price = None
            prev = None

            info = getattr(t, "fast_info", None)
            if info:
                price = (
                    info.get("last_price")
                    or info.get("lastPrice")
                    or info.get("regularMarketPrice")
                )
                prev = info.get("previous_close") or info.get(
                    "regularMarketPreviousClose"
                )

            try:
                data = t.info if price is None or prev is None else {}
            except Exception:  # network issues or invalid ticker
                data = {}

            if price is None:
                price = data.get("regularMarketPrice") or data.get("currentPrice")
            if prev is None:
                prev = data.get("regularMarketPreviousClose") or data.get(
                    "previousClose"
                )

            if price is None or prev is None:
                hist = t.history(period="2d")
                if not hist.empty:
                    price = price or hist["Close"].iloc[-1]
                    if prev is None and len(hist["Close"]) > 1:
                        prev = hist["Close"].iloc[-2]

            def clean(val):
                return (
                    None
                    if val is None or (isinstance(val, float) and (val != val))
                    else float(val)
                )

            price = clean(price)
            prev = clean(prev)

            change = None
            pct = None
            if price is not None and prev is not None and prev != 0:
                change = price - prev
                pct = (change / prev) * 100

            quotes.append(
                {
                    "symbol": sym,
                    "price": price,
                    "change": change,
                    "change_percent": pct,
                }
            )
        except Exception as e:
            logger.exception("Failed to fetch quote for %s", sym)
            quotes.append({"symbol": sym, "error": str(e)})
    logger.debug("Returning %d quotes", len(quotes))
    return ApiResponse(success=True, data=quotes)


@router.get("/symbols", response_model=ApiResponse)
def get_available_symbols():
    """Get list of available stock symbols from CSV files."""
    logger.info("Fetching available stock symbols")
    try:
        symbols = get_available_stocks()
        logger.debug(f"Found {len(symbols)} symbols")
        return ApiResponse(success=True, data=symbols)
    except Exception as e:
        logger.exception("Failed to fetch available symbols")
        return ApiResponse(success=False, error=str(e))


@router.get("/daily/{symbol}", response_model=ApiResponse)
def get_daily_data(
    symbol: str,
    start_date: str | None = Query(None),
    end_date: str | None = Query(None)
):
    """Get daily OHLCV data for a symbol."""
    logger.info(f"Fetching daily data for {symbol}")
    try:
        data = load_daily_stock_data(symbol, start_date, end_date)
        logger.debug(f"Returning {len(data)} daily records for {symbol}")
        return ApiResponse(success=True, data=data)
    except Exception as e:
        logger.exception(f"Failed to fetch daily data for {symbol}")
        return ApiResponse(success=False, error=str(e))


@router.get("/intraday/{symbol}", response_model=ApiResponse)
def get_intraday_data(
    symbol: str,
    start_date: str | None = Query(None),
    end_date: str | None = Query(None)
):
    """Get 5-minute OHLCV data for a symbol."""
    logger.info(f"Fetching intraday data for {symbol}")
    try:
        data = load_intraday_stock_data(symbol, start_date, end_date)
        logger.debug(f"Returning {len(data)} intraday records for {symbol}")
        return ApiResponse(success=True, data=data)
    except Exception as e:
        logger.exception(f"Failed to fetch intraday data for {symbol}")
        return ApiResponse(success=False, error=str(e))


@router.get("/data/{symbol}/{date}", response_model=ApiResponse)
def get_stock_data_by_date(symbol: str, date: str):
    """Get both daily and intraday data for a symbol on a specific date."""
    logger.info(f"Fetching stock data for {symbol} on {date}")
    try:
        data = get_stock_data_for_date(symbol, date)
        return ApiResponse(success=True, data=data)
    except Exception as e:
        logger.exception(f"Failed to fetch stock data for {symbol} on {date}")
        return ApiResponse(success=False, error=str(e))
