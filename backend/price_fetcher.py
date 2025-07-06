import yfinance as yf
from db_insert import insert_price, log_signal
from alert import send_alert
import config
import os

def get_price_from_yahoo(ticker):
    stock = yf.Ticker(ticker)
    # Requesting only 1 hour of data, 1 bar
    data = stock.history(period="1h", interval="60m")

    if data.empty:
        print(f"No data found for {ticker}")
        return None, None, None

    last_price = data['Close'].iloc[-1]
    open_price = data['Open'].iloc[-1]
    volume = data['Volume'].iloc[-1]

    return round(float(last_price), 2), round(float(open_price), 2), int(volume)

def fetch_and_store_all():
    # Tickers loaded from environment variable for AWS/prod
    tickers_env = os.environ.get("TICKERS")
    if tickers_env:
        tickers = [t.strip() for t in tickers_env.split(",") if t.strip()]
        if not tickers:
            print("TICKERS env var provided but is empty.")
            return
    else:
        # Fallback default list (for local/dev)
        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "^SPX", "BTC-USD", "ETH-USD", "SOL-USD"]

    for symbol in tickers:
        price, open_price, volume = get_price_from_yahoo(symbol)
        if price is not None and open_price is not None and volume is not None:
            pct_change = (price - open_price) / open_price
            if pct_change >= 0.03:
                print(f"{symbol} is UP {pct_change:.2%} since open (${open_price} → ${price})")
                log_signal(symbol, "OPEN_UP", price)
                send_alert(f"{symbol} is UP {pct_change:.2%} since open (${open_price} → ${price})", config.DISCORD_WEBHOOK)
            elif pct_change <= -0.03:
                print(f"{symbol} is DOWN {pct_change:.2%} since open (${open_price} → ${price})")
                log_signal(symbol, "OPEN_DOWN", price)
                send_alert(f"{symbol} is DOWN {pct_change:.2%} since open (${open_price} → ${price})", config.DISCORD_WEBHOOK)

            insert_price(symbol, price, volume)

def main():
    print("Starting price fetcher (single run)...")
    fetch_and_store_all()
    print("Fetcher complete.")

if __name__ == "__main__":
    main()
