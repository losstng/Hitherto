import pytest
from backend.routers.stocks import get_stock_quotes
import yfinance as yf

class DummyTicker:
    def __init__(self, symbol):
        self.info = {
            "regularMarketPrice": 10.0,
            "regularMarketPreviousClose": 8.0,
        }
        self.fast_info = None

def test_get_stock_quotes(monkeypatch):
    monkeypatch.setattr(yf, "Ticker", DummyTicker)
    resp = get_stock_quotes(tickers="TEST")
    assert resp.success is True
    assert resp.data[0]["symbol"] == "TEST"
    assert resp.data[0]["price"] == 10.0
    assert abs(resp.data[0]["change_percent"] - 25.0) < 1e-6

