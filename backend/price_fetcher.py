import yfinance as yf 
from db_insert import insert_price, log_signal
import time 
from alert import send_alert
import config

def get_price_from_yahoo(ticker):
    stock = yf.Ticker(ticker)
    todays_data = stock.history(period = "1d")

    if todays_data.empty:
        print(f"No data found for {ticker}")
        return None, None, None
    
    last_price = todays_data['Close'].iloc[-1]
    open_price = todays_data['Open'].iloc[-1]
    volume = todays_data['Volume'].iloc[-1]

    return round(float(last_price), 2), round(float(open_price), 2), int(volume)

def fetch_and_store_all():
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

            #Insert into DB only after analysis
            insert_price(symbol, price, volume)

print("Starting price fetcher... Press Ctrl+C to stop.")
try:
    while True:
        fetch_and_store_all()
        print("Cycle complete. Sleeping 5 minutes...\n")
        time.sleep(300)

except KeyboardInterrupt:
    print("Stopped by user")
