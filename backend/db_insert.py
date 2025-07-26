import psycopg2
import config
from alert import send_alert

# Insert the latest price into the database, with signal checks
def insert_price(ticker, new_price, volume, timestamp, conn=None, cursor=None):
    close_conn = False
    try:
        # Reuse connection/cursor if passed; else open new one
        if conn is None or cursor is None:
            conn = psycopg2.connect(
                dbname=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                host=config.DB_HOST,
                port=config.DB_PORT
            )
            cursor = conn.cursor()
            close_conn = True

        # Deduplication: rely on DB unique constraint (ticker, timestamp)
        cursor.execute("""
            INSERT INTO prices (ticker, price, volume, timestamp)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (ticker, timestamp) DO NOTHING;
        """, (ticker, new_price, volume, timestamp))
        print(f"Inserted {ticker} @ ${new_price} at {timestamp}")

        # Clean up old prices (older than 90 days)
        cursor.execute("""
            DELETE FROM prices
            WHERE ticker = %s AND timestamp < NOW() - INTERVAL '90 days';
        """, (ticker,))

        if close_conn:
            conn.commit()

    except Exception as e:
        print("Insert failed:", e)

    finally:
        if close_conn:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()

# Retrieve the last N price values for a ticker
def get_last_n_prices(ticker, n, conn=None, cursor=None):
    close_conn = False
    try:
        if conn is None or cursor is None:
            conn = psycopg2.connect(
                dbname=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                host=config.DB_HOST,
                port=config.DB_PORT
            )
            cursor = conn.cursor()
            close_conn = True

        cursor.execute("""
            SELECT price FROM prices
            WHERE ticker = %s 
            ORDER BY timestamp DESC
            LIMIT %s
        """, (ticker, n))

        results = cursor.fetchall()
        return [float(row[0]) for row in results]

    except Exception as e: 
        print("Failed to get past prices:", e)
        return []
    
    finally:
        if close_conn:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()

# Record signal events in 'signals' table
def log_signal(ticker, signal_type, price, conn=None, cursor=None):
    close_conn = False
    try:
        if conn is None or cursor is None:
            conn = psycopg2.connect(
                dbname=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                host=config.DB_HOST,
                port=config.DB_PORT
            )
            cursor = conn.cursor()
            close_conn = True

        cursor.execute("""
            INSERT INTO signals (ticker, type, price, timestamp)
            VALUES (%s, %s, %s, NOW());
        """, (ticker, signal_type, price))

        if close_conn:
            conn.commit()
        print(f"Logged signal: {ticker} {signal_type} @ ${price}")

    except Exception as e:
        print("Failed to log signal:", e)

    finally:
        if close_conn:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()

# Create the 'generated_signals' table if it doesn't exist
def create_generated_signals_table():
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
            CREATE TABLE IF NOT EXISTS generated_signals (
                id SERIAL PRIMARY KEY,
                ticker TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                signal_value REAL,
                signal_strength TEXT,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("✅ generated_signals table is ready")

    except Exception as e:
        print("Failed to create generated_signals table:", e)

    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()
