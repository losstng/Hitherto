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


from ..schemas import ApiResponse
import logging
import importlib

try:  # pragma: no cover - optional dependency
    import yfinance as yf
except Exception:
    yf = importlib.import_module("yfinance") if "yfinance" in globals() else None

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_TICKERS = [
    "INOD",
    "TSLA",
    "MRVL",
    "AMD",
    "NVDA",
    "PLTR",
    "DAVE",
    "HAG.DE",
    "GC=F",
]


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
