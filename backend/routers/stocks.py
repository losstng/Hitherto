from fastapi import APIRouter, Query
from ..schemas import ApiResponse
import yfinance as yf
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_TICKERS = ["TSLA", "GLOB", "MRVL", "NVDA", "INOD", "PLTR", "DAVE"]

@router.get("/quotes", response_model=ApiResponse)
def get_stock_quotes(tickers: str | None = Query(None)):
    symbols = tickers.split(",") if tickers else DEFAULT_TICKERS
    quotes = []
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            info = getattr(t, "fast_info", None)
            price = None
            prev = None
            if info:
                price = info.get("last_price") or info.get("lastPrice") or info.get("regularMarketPrice")
                prev = info.get("previous_close") or info.get("regularMarketPreviousClose")
            if price is None or prev is None:
                data = t.info
                price = price or data.get("regularMarketPrice")
                prev = prev or data.get("regularMarketPreviousClose")
            change = None
            pct = None
            if price is not None and prev is not None and prev != 0:
                change = price - prev
                pct = (change / prev) * 100
            quotes.append({
                "symbol": sym,
                "price": price,
                "change": change,
                "change_percent": pct,
            })
        except Exception as e:
            logger.exception("Failed to fetch quote for %s", sym)
            quotes.append({"symbol": sym, "error": str(e)})
    return ApiResponse(success=True, data=quotes)

