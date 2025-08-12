import pandas as pd
import numpy as np
from datetime import datetime
from plot_prices import fetch_price_history

from db_insert import insert_signal

def insert_generated_signal(
    ticker: str,
    signal_type: str,
    timestamp,
    signal_value,
    signal_strength,          # 'BUY' | 'SELL' | 'NEUTRAL' (from your current code)
    *,
    triggered_by: str = "manual",
    params: dict | None = None,
    message: str | None = None,
    confidence: float | None = None,
    strength: str | None = None
):
    """
    Adapter: keep existing call sites but write to the unified `signals` table.
    - Maps `signal_strength` -> `action`
    - Passes through value/params/timestamp
    - Leaves confidence optional for now
    """
    action = signal_strength if signal_strength in ("BUY", "SELL") else "NEUTRAL"
    # Default strength lightly derived unless caller overrides
    final_strength = strength or ("high" if action in ("BUY", "SELL") else "low")

    # Minimal, readable message if none provided
    if not message:
        message = f"{ticker} {signal_type} → {action} (value={signal_value})"

    insert_signal(
        ticker=ticker,
        signal_type=signal_type,
        action=action,
        signal_value=float(signal_value) if signal_value is not None else None,
        confidence=confidence,
        strength=final_strength,
        params=params,
        triggered_by=triggered_by,
        message=message,
        timestamp=timestamp
    )

# === SIGNAL CALCULATIONS ===
def calculate_macd(data):
    exp1 = data['close'].ewm(span=12, adjust=False).mean()
    exp2 = data['close'].ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram

def calculate_bollinger(data, window=20):
    sma = data['close'].rolling(window).mean()
    std = data['close'].rolling(window).std()
    upper_band = sma + (std * 2)
    lower_band = sma - (std * 2)
    return sma, upper_band, lower_band

def calculate_ma_cross(data, short=50, long=200):
    short_ma = data['close'].rolling(window=short).mean()
    long_ma = data['close'].rolling(window=long).mean()
    cross = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
    death = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
    return short_ma, long_ma, cross, death

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def generate_signals(ticker):
    df = fetch_price_history(ticker)
    if df.empty or len(df) < 200:
        print(f"Not enough data for {ticker}")
        return

    df['close'] = df['price']  # Standardize column
    df['volume'] = 1e6  # TEMPORARY: Assume volume exists (replace with real if available)
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)

    latest_time = df.index[-1]
    latest_price = df['close'].iloc[-1]

    # MACD
    macd_line, _, _ = calculate_macd(df)
    if not macd_line.empty:
        latest_macd = macd_line.iloc[-1]
        signal_strength_macd = 'BUY' if latest_macd > 0 else 'SELL'
        insert_generated_signal(ticker, 'MACD', latest_time, latest_macd, signal_strength_macd)

    # Bollinger
    _, upper, lower = calculate_bollinger(df)
    if not upper.empty and not lower.empty:
        if latest_price > upper.iloc[-1]:
            insert_generated_signal(ticker, 'BOLLINGER', latest_time, latest_price, 'SELL')
        elif latest_price < lower.iloc[-1]:
            insert_generated_signal(ticker, 'BOLLINGER', latest_time, latest_price, 'BUY')
        else:
            insert_generated_signal(ticker, 'BOLLINGER', latest_time, latest_price, 'NEUTRAL')

    # MA Cross (Golden/Death)
    _, _, cross, death = calculate_ma_cross(df)
    if not cross.empty and not death.empty:
        if cross.iloc[-1]:
            insert_generated_signal(ticker, 'GOLDEN_CROSS', latest_time, latest_price, 'BUY')
        elif death.iloc[-1]:
            insert_generated_signal(ticker, 'DEATH_CROSS', latest_time, latest_price, 'SELL')
        else:
            insert_generated_signal(ticker, 'MA_CROSS', latest_time, latest_price, 'NEUTRAL')

    # Volume
    if 'volume' in df.columns and len(df['volume'].dropna()) >= 20:
        avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
        latest_volume = df['volume'].iloc[-1]
        direction = 'UP' if latest_price > df['close'].iloc[-2] else 'DOWN'
        if latest_volume > 1.5 * avg_volume:
            insert_generated_signal(ticker, 'VOLUME', latest_time, latest_volume, 'BUY' if direction == 'UP' else 'SELL')
        else:
            insert_generated_signal(ticker, 'VOLUME', latest_time, latest_volume, 'NEUTRAL')

    # RSI
    rsi = calculate_rsi(df['close'])
    if not rsi.empty:
        rsi_value = rsi.iloc[-1]
        if rsi_value > 70:
            rsi_strength = 'SELL'
        elif rsi_value < 30:
            rsi_strength = 'BUY'
        else:
            rsi_strength = 'NEUTRAL'
        insert_generated_signal(ticker, 'RSI', latest_time, rsi_value, rsi_strength)

    # Auto-delete old generated signals (older than 90 days)
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
            DELETE FROM generated_signals
            WHERE timestamp < NOW() - INTERVAL '90 days';
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Failed to clean old generated signals:", e)

