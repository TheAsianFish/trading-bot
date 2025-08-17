import psycopg2
import json
import config

# Insert (idempotent) price bar
def insert_price(ticker, new_price, volume, timestamp, conn=None, cursor=None):
    close_conn = False
    try:
        if conn is None or cursor is None:
            conn = psycopg2.connect(
                dbname=config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD,
                host=config.DB_HOST, port=config.DB_PORT
            )
            cursor = conn.cursor()
            close_conn = True

        cursor.execute("""
            INSERT INTO prices (ticker, price, volume, timestamp)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (ticker, timestamp) DO NOTHING;
        """, (ticker, new_price, volume, timestamp))

        # keep last 90 days per ticker
        cursor.execute("DELETE FROM prices WHERE ticker=%s AND timestamp < NOW() - INTERVAL '90 days';", (ticker,))

        if close_conn:
            conn.commit()
        print(f"Inserted {ticker} @ {new_price} at {timestamp}")
    except Exception as e:
        print("Insert failed:", e)
    finally:
        if close_conn:
            try: cursor.close()
            except: pass
            try: conn.close()
            except: pass


def get_last_n_prices(ticker, n, conn=None, cursor=None):
    close_conn = False
    try:
        if conn is None or cursor is None:
            conn = psycopg2.connect(
                dbname=config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD,
                host=config.DB_HOST, port=config.DB_PORT
            )
            cursor = conn.cursor()
            close_conn = True

        cursor.execute("""
            SELECT price FROM prices
            WHERE ticker=%s
            ORDER BY timestamp DESC
            LIMIT %s;
        """, (ticker, n))
        rows = cursor.fetchall()
        return [float(r[0]) for r in rows]
    except Exception as e:
        print("Failed to get past prices:", e)
        return []
    finally:
        if close_conn:
            try: cursor.close()
            except: pass
            try: conn.close()
            except: pass


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
    timestamp=None,        # human-facing time (we pass bar close)
    strategy=None,
    bar_ts=None,           # NEW: candle close time for dedupe
    conn=None,
    cursor=None
):
    """
    Insert or update a row in `signals`. Enforces one row per
    (ticker, signal_type, strategy, bar_ts).
    """
    close_conn = False
    try:
        if conn is None or cursor is None:
            conn = psycopg2.connect(
                dbname=config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD,
                host=config.DB_HOST, port=config.DB_PORT
            )
            cursor = conn.cursor()
            close_conn = True

        cursor.execute("""
            INSERT INTO signals (
                ticker, signal_type, strategy, action,
                signal_value, confidence, strength, params,
                triggered_by, message, timestamp, bar_ts
            )
            VALUES (
                %(ticker)s, %(signal_type)s, %(strategy)s, %(action)s,
                %(signal_value)s, %(confidence)s, %(strength)s, %(params)s,
                %(triggered_by)s, %(message)s, COALESCE(%(timestamp)s, NOW()), %(bar_ts)s
            )
            ON CONFLICT (ticker, signal_type, COALESCE(strategy,''), bar_ts)
            DO UPDATE SET
                action       = EXCLUDED.action,
                signal_value = EXCLUDED.signal_value,
                confidence   = EXCLUDED.confidence,
                strength     = EXCLUDED.strength,
                params       = EXCLUDED.params,
                triggered_by = EXCLUDED.triggered_by,
                message      = EXCLUDED.message,
                timestamp    = EXCLUDED.timestamp
            ;
        """, {
            "ticker": ticker,
            "signal_type": signal_type,
            "strategy": strategy,
            "action": action,
            "signal_value": signal_value,
            "confidence": confidence,
            "strength": strength,
            "params": json.dumps(params) if params else None,
            "triggered_by": triggered_by,
            "message": message or "",
            "timestamp": timestamp,
            "bar_ts": bar_ts or timestamp,  # keep in sync if only timestamp is passed
        })

        if close_conn:
            conn.commit()
        print(f"Inserted signal: {ticker} {signal_type}/{action} value={signal_value}")
    except Exception as e:
        print("Failed to log signal:", e)
    finally:
        if close_conn:
            try: cursor.close()
            except: pass
            try: conn.close()
            except: pass
