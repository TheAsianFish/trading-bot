# db_setup.py
import psycopg2
import os
import config

DDL = """
CREATE TABLE IF NOT EXISTS prices (
  id SERIAL PRIMARY KEY,
  ticker TEXT NOT NULL,
  price REAL NOT NULL,
  volume BIGINT,
  timestamp TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_prices_t_ts ON prices(ticker, timestamp);
CREATE INDEX IF NOT EXISTS idx_prices_ts ON prices(timestamp);

CREATE TABLE IF NOT EXISTS signals (
  id SERIAL PRIMARY KEY,
  ticker TEXT NOT NULL,
  signal_type TEXT NOT NULL,
  strategy TEXT,
  action TEXT NOT NULL,
  signal_value REAL,
  confidence REAL,
  strength TEXT,
  params JSONB,
  triggered_by TEXT,
  message TEXT,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  bar_ts TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_ticker_ts ON signals (ticker, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_action_ts ON signals (action, timestamp DESC);

-- one row per (ticker/signal/strategy) per bar
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM   pg_indexes
    WHERE  schemaname = 'public'
    AND    indexname  = 'uq_signals_bar'
  ) THEN
    EXECUTE 'CREATE UNIQUE INDEX uq_signals_bar
             ON signals (ticker, signal_type, COALESCE(strategy, ''''), bar_ts)';
  END IF;
END
$$;
"""

def main():
    conn = psycopg2.connect(
        dbname=config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD,
        host=config.DB_HOST, port=config.DB_PORT
    )
    with conn, conn.cursor() as cur:
        cur.execute(DDL)
    print("DB setup complete.")

if __name__ == "__main__":
    main()
