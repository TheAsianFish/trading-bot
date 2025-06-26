import psycopg2
import config
import pandas as pd
import matplotlib.pyplot as plt

def fetch_price_history(ticker):
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        cur = conn.cursor()

        cur.execute("""
            SELECT timestamp, price FROM prices
            WHERE ticker = %s
            ORDER BY timestamp ASC;
        """, (ticker,))

        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=["timestamp", "price"])
        return df

    except Exception as e:
        print("Failed to fetch data:", e)
        return pd.DataFrame()
    
    finally: 
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

#Plotting
def plot_prices(ticker):
    df = fetch_price_history(ticker)

    if df.empty:
        print("No data to plot.")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(df["timestamp"], df["price"], marker="o", linestyle="-")
    plt.title(f"{ticker} Price Over Time")
    plt.xlabel("Time")
    plt.ylabel("Price (USD)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

plot_prices("AAPL")