import os
import yfinance as yf
from db_insert import insert_price
import pandas as pd

def _get_latest_bar(ticker):
    """
    Return (last_price, last_volume, last_timestamp_utc) using 1m data if available,
    otherwise fallback to 60m. Returns (None, None, None) if no data.
    """
    tk = yf.Ticker(ticker)

    intraday = tk.history(period="1d", interval="1m")
    if intraday is None or intraday.empty:
        intraday = tk.history(period="1d", interval="60m")
    if intraday is None or intraday.empty:
        print(f"[yf] No intraday data for {ticker}")
        return None, None, None

    last_row = intraday.iloc[-1]
    last_price = float(last_row.get("Close"))
    last_volume_raw = last_row.get("Volume")
    last_volume = None if pd.isna(last_volume_raw) else int(last_volume_raw)
    last_ts = last_row.name.to_pydatetime()  # ensure psycopg2-friendly tz-aware datetime
    return round(last_price, 4), last_volume, last_ts


def fetch_and_store_all():
    # Resolve tickers
    tickers_env = os.environ.get("TICKERS")
    if tickers_env:
        tickers = [t.strip() for t in tickers_env.split(",") if t.strip()]
        if not tickers:
            print("TICKERS env var provided but empty.")
            return
    else:
        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA",
                   "^GSPC", "BTC-USD", "ETH-USD", "SOL-USD"]

    for symbol in tickers:
        try:
            last_price, last_volume, ts = _get_latest_bar(symbol)
            if last_price is None or ts is None:
                print(f"[skip] No data for {symbol}")
                continue

            # Ingest only — no signals or alerts here
            try:
                insert_price(symbol, last_price, last_volume, ts)
                print(f"[prices] inserted {symbol} @ {last_price} ({ts})")
            except Exception as ie:
                print(f"[prices] insert failed for {symbol}: {ie}")

        except Exception as e:
            print(f"[loop] failed for {symbol}: {e}")


def main():
    print("Starting price fetcher (ingestion only)…")
    fetch_and_store_all()
    print("Done.")

if __name__ == "__main__":
    main()
