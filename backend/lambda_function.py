# lambda handler for price fetcher
import os
import psycopg2
from db_insert import insert_price, log_signal  # Import your own logic!
import yfinance as yf

def lambda_handler(event, context):
    # List of tickers
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "^SPX", "BTC-USD", "ETH-USD", "SOL-USD"]
    
    # You can get DB credentials from environment variables in Lambda's config
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_host = os.environ['DB_HOST']
    db_port = os.environ['DB_PORT']

    # Set up database connection
    conn = psycopg2.connect(
        dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port
    )
    cursor = conn.cursor()

    def get_price_from_yahoo(ticker):
        stock = yf.Ticker(ticker)
        data = stock.history(period="1h", interval="60m")
        if data.empty:
            return None, None, None
        last_price = data['Close'].iloc[-1]
        open_price = data['Open'].iloc[-1]
        volume = data['Volume'].iloc[-1]
        return round(float(last_price), 2), round(float(open_price), 2), int(volume)

    for symbol in tickers:
        price, open_price, volume = get_price_from_yahoo(symbol)
        if price is not None and open_price is not None and volume is not None:
            # Here call your insert_price or raw SQL insert
            insert_price(symbol, price, volume, conn, cursor)  # Adjust for Lambda context!
    
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success"}
