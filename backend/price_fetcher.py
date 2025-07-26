import yfinance as yf
from db_insert import insert_price, log_signal
from alert import send_alert
import config
import os

def get_price_from_yahoo(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d", interval="60m")

    if data.empty:
        print(f"No data found for {ticker}")
        return None, None, None, None

    last_bar = data.iloc[-1]
    last_price = last_bar['Close']
    open_price = last_bar['Open']
    volume = last_bar['Volume']
    timestamp = last_bar.name  # This is a pandas.Timestamp (UTC)

    return round(float(last_price), 2), round(float(open_price), 2), int(volume), timestamp

def fetch_and_store_all():
    tickers_env = os.environ.get("TICKERS")
    if tickers_env:
        tickers = [t.strip() for t in tickers_env.split(",") if t.strip()]
        if not tickers:
            print("TICKERS env var provided but is empty.")
            return
    else:
        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "^SPX", "BTC-USD", "ETH-USD", "SOL-USD"]

    for symbol in tickers:
        try:
            price, open_price, volume, timestamp = get_price_from_yahoo(symbol)
            if price is not None and open_price is not None and volume is not None:
                pct_change = (price - open_price) / open_price
                if pct_change >= 0.03:
                    print(f"{symbol} is UP {pct_change:.2%} since open (${open_price} → ${price})")
                    try:
                        log_signal(symbol, "OPEN_UP", price)
                        send_alert(f"{symbol} is UP {pct_change:.2%} since open (${open_price} → ${price})", config.DISCORD_WEBHOOK)
                    except Exception as se:
                        print(f"Signal or alert failed for {symbol}: {se}")
                elif pct_change <= -0.03:
                    print(f"{symbol} is DOWN {pct_change:.2%} since open (${open_price} → ${price})")
                    try:
                        log_signal(symbol, "OPEN_DOWN", price)
                        send_alert(f"{symbol} is DOWN {pct_change:.2%} since open (${open_price} → ${price})", config.DISCORD_WEBHOOK)
                    except Exception as se:
                        print(f"Signal or alert failed for {symbol}: {se}")

                try:
                    insert_price(symbol, price, volume, timestamp)
                    print(f"Inserted price for {symbol} at {timestamp}")
                except Exception as ie:
                    print(f"Insert failed for {symbol}: {ie}")
        except Exception as e:
            print(f"Failed to process {symbol}: {e}")

def main():
    print("Starting price fetcher (single run)...")
    fetch_and_store_all()
    print("Fetcher complete.")

if __name__ == "__main__":
    main()
