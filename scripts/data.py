import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import date, timedelta
import datetime

# --- Setup: Root paths and folders ---
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "raw_data" / "intraday"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR_1 = REPO_ROOT / "raw_data" 
DATA_DIR_1.mkdir(parents=True, exist_ok=True)

START_DATE = date.today() - timedelta(days=30)

def update_intraday_csv(ticker: str):
    """
    Fetches the most recent 1-minute intraday data for a given ticker,
    and saves or appends it to 'intraday_{ticker}.csv'.
    """
    filepath = DATA_DIR / f"intraday_{ticker}.csv"

    # If file exists, load it; else, create an empty DataFrame
    if filepath.exists():
        old_df = pd.read_csv(filepath, parse_dates=True, index_col='Datetime')
        last_date = old_df.index.max().date() if not old_df.empty else START_DATE
    else:
        old_df = pd.DataFrame()
        last_date = START_DATE

    start_date = last_date + timedelta(days=1)
    end_date = start_date + timedelta(days=8)

    print(f"Fetching {ticker} from {start_date} to {end_date}...")

    df = yf.Ticker(ticker).history(start=start_date, end=end_date, interval="1m")

    if df.empty:
        print(f"No new data returned for {ticker}.")
        if not old_df.empty:
            old_df.to_csv(filepath)
        return

    df.index.name = 'Datetime'

    if old_df.empty:
        df.to_csv(filepath)
    else:
        merged_df = pd.concat([old_df, df], sort=False)
        merged_df = merged_df[~merged_df.index.duplicated(keep='last')]  # drop duplicate indices
        merged_df.to_csv(filepath)

    print(f"Data for {ticker} saved to {filepath.name}.")

#update_intraday_csv("NVDA") 
#update_intraday_csv("INOD")
#update_intraday_csv("MRVL")  

def update_daily_csv(ticker: str):
    """
    Fetches the most recent daily data for a given ticker and saves/appends it to 'daily_{TICKER}.csv'.
    """

    ticker_cap = ticker.upper()
    filepath = DATA_DIR_1 / f"daily_{ticker_cap}.csv"

    # If file exists, load it; else, create an empty DataFrame
    if filepath.exists():
        old_df = pd.read_csv(filepath, parse_dates=True, index_col='Date')
        last_date = old_df.index.max().date() if not old_df.empty else START_DATE
    else:
        old_df = pd.DataFrame()
        last_date = START_DATE

    start_date = last_date + timedelta(days=1)
    end_date = start_date + timedelta(days=8)

    if start_date > end_date:
        print(f"No update needed for {ticker_cap}: already up to date.")
        return

    print(f"Fetching {ticker_cap} daily data from {start_date} to {end_date}...")

    df = yf.Ticker(ticker).history(start=start_date, end=end_date + timedelta(days=1), interval="1d")

    if df.empty:
        print(f"No new data returned for {ticker_cap}.")
        if not old_df.empty:
            old_df.to_csv(filepath)
        return

    df.index.name = 'Date'
    df = df[~df.index.duplicated(keep='last')]  # Just in case
    df = df[~df.index.isin(old_df.index)] if not old_df.empty else df

    if old_df.empty:
        df.to_csv(filepath)
    else:
        merged_df = pd.concat([old_df, df], sort=False)
        merged_df = merged_df[~merged_df.index.duplicated(keep='last')]
        merged_df.sort_index(inplace=True)
        merged_df.to_csv(filepath)

    print(f"Data for {ticker_cap} saved to {filepath.name}.")
