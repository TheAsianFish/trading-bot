import psycopg2
import json
import config

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

        # Clean up old prices (older than 90 days)
        cursor.execute("""
            DELETE FROM prices
            WHERE ticker = %s AND timestamp < NOW() - INTERVAL '90 days';
        """, (ticker,))

        if close_conn:
            conn.commit()
        print(f"Inserted {ticker} @ ${new_price} at {timestamp}")

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

        rows = cursor.fetchall()
        return [float(r[0]) for r in rows]

    except Exception as e:
        print("Failed to get past prices:", e)
        return []
    
    finally:
        if close_conn:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()

# Unified signals
def insert_signal(
    ticker,
    signal_type,
    action,
    signal_value=None,
    confidence=None,
    strength=None,
    params=None,           # dict -> JSONB
    triggered_by="auto",
    message=None,
    timestamp=None,
    strategy=None,
    conn=None,
    cursor=None
):
    """
    Insert a row into the unified `signals` table.
    All fields map to the new schema; pass only what you need.
    """
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
            INSERT INTO signals (
                ticker, signal_type, strategy, action,
                signal_value, confidence, strength, params,
                triggered_by, message, timestamp
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                COALESCE(%s, NOW())
            );
        """, (
            ticker,
            signal_type,
            strategy,                       # strategy (optional; set later if you use variants)
            action,
            signal_value,
            confidence,
            strength,
            json.dumps(params) if params else None,
            triggered_by,
            message,
            timestamp
        ))

        if close_conn:
            conn.commit()
        print(f"Inserted signal: {ticker} {signal_type}/{action} value={signal_value}")


    except Exception as e:
        print("Failed to log signal:", e)

    finally:
        if close_conn:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()