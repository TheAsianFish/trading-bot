# price_fetcher.py
import os, time, math
from datetime import datetime, timezone
import yfinance as yf
from db_insert import insert_price

TICKERS = [t.strip() for t in os.environ.get("TICKERS", "AAPL,MSFT,GOOGL,TSLA,^GSPC,BTC-USD,ETH-USD,SOL-USD").split(",") if t.strip()]

def _tz_utc(df):
    if df is None or df.empty:
        return df
    return df.tz_localize("UTC") if df.index.tz is None else df.tz_convert("UTC")

def _fetch_hourly_once(ticker: str, period: str, interval: str):
    tk = yf.Ticker(ticker)
    df = tk.history(period=period, interval=interval, auto_adjust=False, actions=False)
    if df is None or df.empty:
        return None
    df = _tz_utc(df)
    # Normalize to hourly frame
    if "Close" in df.columns:
        if interval == "1m":
            h = df["Close"].resample("1H").last().to_frame("price")
            h["volume"] = df["Volume"].resample("1H").sum()
        else:  # 60m already hourly
            h = df["Close"].to_frame("price")
            h["volume"] = df.get("Volume")
        return h.dropna(subset=["price"])
    return None

def _fetch_hourly_with_retry(ticker: str):
    attempts = [
        ("1d",  "1m"),   # best fidelity → resample to 1H
        ("7d", "60m"),   # stable hourly for last week
        ("30d","60m"),   # last resort
    ]
    for (period, interval) in attempts:
        for i in range(3):  # retry 3x per combo
            try:
                h = _fetch_hourly_once(ticker, period, interval)
                if h is not None and not h.empty:
                    print(f"[yf] {ticker} {period}/{interval} → {len(h)} rows")
                    return h
                else:
                    print(f"[yf] empty for {ticker} ({period}/{interval}) try={i+1}")
            except Exception as e:
                print(f"[yf] error {ticker} {period}/{interval} try={i+1}: {e}")
            time.sleep(1.5 * (i + 1))  # backoff
    print(f"[yf] give up {ticker}")
    return None

def fetch_and_store_all():
    total_inserted = 0
    for t in TICKERS:
        h = _fetch_hourly_with_retry(t)
        if h is None or h.empty:
            print(f"[ingest] skip {t}: no data")
            continue
        count = 0
        for ts, row in h.iterrows():
            insert_price(
                ticker=t,
                new_price=float(row["price"]),
                volume=int((row.get("volume") or 0)),
                timestamp=ts.to_pydatetime()
            )
            count += 1
        total_inserted += count
        print(f"[ingest] {t}: wrote {count} hourly bars")
    print(f"[ingest] total={total_inserted}")
