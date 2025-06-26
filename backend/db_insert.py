# db_insert.py

import psycopg2
import config
from alert import send_alert

#Insert the latest price into the database, with signal checks
def insert_price(ticker, new_price, volume):
    try:
        #Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        cur = conn.cursor()

        #Fetch the most recent price for this ticker
        cur.execute("""
            SELECT price FROM prices
            WHERE ticker = %s
            ORDER BY timestamp DESC
            LIMIT 1;
        """, (ticker,))
        result = cur.fetchone()

        if result is not None:
            latest_price = float(result[0])

            #SIGNAL: check for price drop > 5%
            if new_price < latest_price and ((latest_price - new_price) / latest_price) >= 0.05:
                print(f"ALERT: {ticker} dropped >5%: {latest_price} → {new_price}")
                log_signal(ticker, "DROP_ALERT", new_price)
                send_alert(f"{ticker} dropped >%5 from ${latest_price:.2f} to ${new_price:.2f}", config.DISCORD_WEBHOOK)

            #skip if duplicate
            if latest_price == new_price:
                print(f"Skipped duplicate: {ticker} @ ${new_price}")
                return
            
            #SIGNAL: Price crossed below 10-period moving average
            past_prices = get_last_n_prices(ticker, 10)
            if len(past_prices) == 10:
                avg_price = sum(past_prices) / 10
                if new_price < avg_price:
                    print(f"SIGNAL: {ticker} dropped below 10-DMA (${avg_price:.2f})")
                    log_signal(ticker, "MA_CROSS", new_price)
                    send_alert(f"{ticker} crossed below 10-DMA @ ${new_price}", config.DISCORD_WEBHOOK)

        #Insert new price into 'prices' table
        cur.execute("""
            INSERT INTO prices (ticker, price, volume) VALUES (%s, %s, %s);
        """, (ticker, new_price, volume))

        conn.commit()
        print(f"Inserted {ticker} @ ${new_price}")

    except Exception as e:
        print("Insert failed:", e)

    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

#Retrieve the last N price values for a ticker
def get_last_n_prices(ticker, n):
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        cur = conn.cursor()

        #Get most recent N price values, descending order
        cur.execute("""
            SELECT price FROM prices
            WHERE ticker = %s 
            ORDER BY timestamp DESC
            LIMIT %s
        """, (ticker, n))

        results = cur.fetchall()
        return [float(row[0]) for row in results]

    except Exception as e: 
        print("Failed to get past prices:", e)
        return []
    
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

#Record signal events in 'signals' table
def log_signal(ticker, signal_type, price):
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
        cur = conn.cursor()

        #Store the signal with type and price
        cur.execute("""
            INSERT INTO signals (ticker, type, price)
            VALUES (%s, %s, %s);
        """, (ticker, signal_type, price))

        conn.commit()
        print(f"Logged signal: {ticker} {signal_type} @ ${price}")

    except Exception as e:
        print("Failed to log signal:", e)

    finally:
        if 'cur' in locals(): cur.close()
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
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("✅ generated_signals table is ready")

    except Exception as e:
        print("Failed to create generated_signals table:", e)

    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()