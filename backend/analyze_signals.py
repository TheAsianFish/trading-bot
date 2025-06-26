import psycopg2
import config
import pandas as pd

# Connect and pull all signals from the database
def fetch_signals():
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT timestamp, ticker, type, price FROM signals ORDER BY timestamp DESC;")
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=["timestamp", "ticker", "type", "price"])

    except Exception as e:
        print("Failed to fetch signals:", e)
        return pd.DataFrame()

    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# Summary report
def summarize_signals(df):
    if df.empty:
        print("No signals to analyze.")
        return

    print("\n🔎 Signal Counts by Type:")
    print(df["type"].value_counts())

    print("\n📈 Signal Counts by Ticker:")
    print(df["ticker"].value_counts())

    print("\n🕒 Most Recent 5 Signals:")
    print(df.head(5))


# ▶️ Run analysis
df = fetch_signals()
summarize_signals(df)
