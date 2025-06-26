import pandas as pd
import numpy as np
from datetime import datetime
from utils import fetch_price_data
from db import insert_generated_signal

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
    data = fetch_price_data(ticker)
    if data is None or len(data) < 200:
        return

    # MACD
    macd_line, signal_line, _ = calculate_macd(data)
    latest_macd = macd_line.iloc[-1]
    signal_strength_macd = 'BUY' if latest_macd > 0 else 'SELL'
    insert_generated_signal(ticker, 'MACD', data.index[-1], latest_macd, signal_strength_macd)

    # Bollinger Bands
    _, upper_band, lower_band = calculate_bollinger(data)
    latest_price = data['close'].iloc[-1]
    if latest_price > upper_band.iloc[-1]:
        insert_generated_signal(ticker, 'BOLLINGER', data.index[-1], latest_price, 'SELL')
    elif latest_price < lower_band.iloc[-1]:
        insert_generated_signal(ticker, 'BOLLINGER', data.index[-1], latest_price, 'BUY')
    else:
        insert_generated_signal(ticker, 'BOLLINGER', data.index[-1], latest_price, 'NEUTRAL')

    # Volume Spike
    latest_volume = data['volume'].iloc[-1]
    avg_volume = data['volume'].rolling(window=20).mean().iloc[-1]
    if latest_volume > 1.5 * avg_volume:
        direction = 'UP' if latest_price > data['close'].iloc[-2] else 'DOWN'
        insert_generated_signal(ticker, 'VOLUME', data.index[-1], latest_volume, 'BUY' if direction == 'UP' else 'SELL')
    else:
        insert_generated_signal(ticker, 'VOLUME', data.index[-1], latest_volume, 'NEUTRAL')

    # Golden / Death Cross
    _, _, golden_cross, death_cross = calculate_ma_cross(data)
    if golden_cross.iloc[-1]:
        insert_generated_signal(ticker, 'GOLDEN_CROSS', data.index[-1], latest_price, 'BUY')
    elif death_cross.iloc[-1]:
        insert_generated_signal(ticker, 'DEATH_CROSS', data.index[-1], latest_price, 'SELL')
    else:
        insert_generated_signal(ticker, 'MA_CROSS', data.index[-1], latest_price, 'NEUTRAL')

    # RSI
    rsi = calculate_rsi(data['close'])
    rsi_value = rsi.iloc[-1]
    if rsi_value > 70:
        strength = 'SELL'
    elif rsi_value < 30:
        strength = 'BUY'
    else:
        strength = 'NEUTRAL'
    insert_generated_signal(ticker, 'RSI', data.index[-1], rsi_value, strength)
