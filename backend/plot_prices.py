import psycopg2
import config
import pandas as pd

def fetch_price_history(ticker: str) -> pd.DataFrame:
    """
    Returns DataFrame with columns ['timestamp','price'] ASC.
    """
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD,
            host=config.DB_HOST, port=config.DB_PORT
        )
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, price
                FROM prices
                WHERE ticker = %s
                ORDER BY timestamp ASC
            """, (ticker,))
            rows = cur.fetchall()
        return pd.DataFrame(rows, columns=["timestamp", "price"])
    except Exception as e:
        print("Failed to fetch data:", e)
        return pd.DataFrame()
