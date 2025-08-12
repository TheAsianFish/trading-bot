# db_setup.py
import psycopg2
import config

DDL = """
-- PRICES: align with code expectations
CREATE TABLE IF NOT EXISTS prices (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    price NUMERIC NOT NULL,           -- keep as NUMERIC for precision
    volume BIGINT,                    -- added; insert_price() writes this
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enforce dedup. Unique index is fine (acts like a unique constraint).
CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_ticker_ts_unique
    ON prices (ticker, timestamp);

-- Helpful read indices
CREATE INDEX IF NOT EXISTS idx_prices_ticker_ts
    ON prices (ticker, timestamp DESC);

-- SIGNALS: unified, same schema you created via pgAdmin
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    signal_type TEXT NOT NULL,        -- e.g., THRESHOLD, MACD, RSI
    strategy TEXT,                    -- optional
    action TEXT NOT NULL,             -- BUY | SELL | NEUTRAL
    signal_value REAL,                -- raw reading (rsi, pct change, macd value)
    confidence REAL,                  -- 0..1 optional
    strength TEXT,                    -- high | medium | low
    params JSONB,                     -- optional bag
    triggered_by TEXT,                -- auto | manual
    message TEXT,                     -- human-readable
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Helpful read indices
CREATE INDEX IF NOT EXISTS idx_signals_ts
    ON signals (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_signals_ticker_ts
    ON signals (ticker, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_signals_action_ts
    ON signals (action, timestamp DESC);
"""

def main():
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        cur = conn.cursor()
        cur.execute(DDL)
        conn.commit()
        print("✅ Schema ensured: prices + signals (with indexes).")
    except Exception as e:
        print("❌ db_setup failed:", e)
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    main()
