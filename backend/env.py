import os

from dotenv import load_dotenv

load_dotenv()


def _as_list(value: str | None):
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


DATABASE_URL = os.getenv("DATABASE_URL")
GMAIL_SCOPE = os.getenv("GMAIL_SCOPE")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", os.getenv("PORT", "8000")))
MODEL_IN_USE = os.getenv("MODEL_IN_USE", "gpt-3.5-turbo")

EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "long131005@gmail.com")
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "HithertoApp/0.1 (hello@example.com)")
SEC_MONITOR_INTERVAL = int(os.getenv("SEC_MONITOR_INTERVAL", "300"))
SEC_EMAIL_RECIPIENT = os.getenv("SEC_EMAIL_RECIPIENT", EMAIL_RECIPIENT)

PRICE_EMAIL_TICKERS = _as_list(os.getenv("PRICE_EMAIL_TICKERS"))
PRICE_EMAIL_RECIPIENT = os.getenv("PRICE_EMAIL_RECIPIENT", EMAIL_RECIPIENT)
PRICE_EMAIL_INTERVAL = int(os.getenv("PRICE_EMAIL_INTERVAL", "300"))
PRICE_CACHE_FILE = os.getenv("PRICE_CACHE_FILE", "stock_prices_cache.json")
PRICE_THREAD_FILE = os.getenv("PRICE_THREAD_FILE", "stock_price_thread.json")

VOLUME_TICKERS = _as_list(os.getenv("VOLUME_TICKERS"))
VOLUME_EMAIL_RECIPIENT = os.getenv("VOLUME_EMAIL_RECIPIENT", EMAIL_RECIPIENT)
VOLUME_MONITOR_INTERVAL = int(os.getenv("VOLUME_MONITOR_INTERVAL", "300"))
VOLUME_DATA_DIR = os.getenv("VOLUME_DATA_DIR", "raw_data/5_min")
VOLUME_ALERT_FILE = os.getenv("VOLUME_ALERT_FILE", "volume_alerts.json")
DEFAULT_TICKERS = _as_list(
    os.getenv("DEFAULT_TICKERS", "INOD,MRVL,TSLA,PLTR,NVDA,GC=F")
)
STOCK_DEFAULT_TICKERS = _as_list(
    os.getenv(
        "STOCK_DEFAULT_TICKERS",
        "INOD,TSLA,MRVL,AMD,NVDA,PLTR,DAVE,HAG.DE,GC=F,LMT",
    )
)

FAISS_STORE_DIR = os.getenv("FAISS_STORE_DIR", "db/faiss_store")
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
CORS_ALLOW_ORIGINS = _as_list(os.getenv("CORS_ALLOW_ORIGINS", "*")) or ["*"]

GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")

EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")
HF_MODEL_DIR = os.getenv("HF_MODEL_DIR")
