import psycopg2
import config
import pandas as pd

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
        print("❌ Error fetching data:", e)
        return pd.DataFrame()
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

def backtest_strategy(ticker):
    df = fetch_price_history(ticker)

    if df.empty or len(df) < 11:
        print("❌ Not enough data to backtest.")
        return

    #Calculate 10-period moving average
    df["ma10"] = df["price"].rolling(window=10).mean()

    in_position = False
    entry_price = 0
    trades = []
    profit = 0

    #Loop through each row and apply the rule
    for i in range(10, len(df)):
        price = df["price"].iloc[i]
        ma10 = df["ma10"].iloc[i]
        time = df["timestamp"].iloc[i]

        # Buy signal
        if not in_position and price < ma10:
            in_position = True
            entry_price = price
            trades.append(f"🟢 BUY @ ${price:.2f} on {time}")

        # Sell signal
        elif in_position and price > ma10:
            in_position = False
            exit_price = price
            trade_profit = exit_price - entry_price
            profit += trade_profit
            trades.append(f"🔴 SELL @ ${price:.2f} on {time} → PnL: ${trade_profit:.2f}")

    # Final summary
    print("\n".join(trades))
    print(f"\n📊 TOTAL PnL for {ticker}: ${profit:.2f}")


backtest_strategy("BTC-USD")
