import pandas as pd
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
# All functions assume a DataFrame `data` with:
# - column 'close' (float)
# - DateTimeIndex sorted ASC (tz-aware preferred; UTC is fine)
# Volume is NOT required here.

# ---------- Core indicator calculations (vectorized, minimal deps) ----------

def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Returns (macd_line, signal_line, macd_histogram)
    macd_line = EMA(fast) - EMA(slow)
    signal_line = EMA(macd_line, signal)
    """
    close = data['close']
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist


def calculate_bollinger(data: pd.DataFrame, window: int = 20, k: float = 2.0):
    """
    Returns (sma, upper_band, lower_band) using population std (ddof=0) and min_periods=window.
    Mean-reversion vs breakout is a decision in the signal function, not here.
    """
    close = data['close']
    sma = close.rolling(window, min_periods=window).mean()
    std = close.rolling(window, min_periods=window).std(ddof=0)
    upper_band = sma + k * std
    lower_band = sma - k * std
    return sma, upper_band, lower_band


def calculate_ma_cross(data: pd.DataFrame, short: int = 50, long: int = 200):
    """
    Returns (short_ma, long_ma, cross_up, cross_down)
    cross_up   True when short crosses above long on the latest bar
    cross_down True when short crosses below long on the latest bar
    """
    close = data['close']
    short_ma = close.rolling(short, min_periods=short).mean()
    long_ma  = close.rolling(long,  min_periods=long).mean()

    prev_above = short_ma.shift(1) > long_ma.shift(1)
    curr_above = short_ma > long_ma
    cross_up   = (~prev_above) & curr_above
    cross_down = prev_above & (~curr_above)

    return short_ma, long_ma, cross_up, cross_down


def calculate_rsi(close: pd.Series, period: int = 14):
    """
    Wilder's RSI (standard): uses EMA smoothing with alpha=1/period.
    Returns a Series of RSI values (NaN until min_periods reached).
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# ---------- Additional lightweight calcs for added signals ----------

def calculate_sma_zscore(data: pd.DataFrame, window: int = 20, ddof: int = 0):
    """
    Returns (sma, std, z) where z = (close - sma) / std.
    """
    close = data['close']
    sma = close.rolling(window, min_periods=window).mean()
    std = close.rolling(window, min_periods=window).std(ddof=ddof)
    z = (close - sma) / std
    return sma, std, z


def calculate_close_breakout(data: pd.DataFrame, window: int = 20, use_previous: bool = True):
    """
    Returns (roll_max, roll_min, breakout_up, breakout_down)
    If use_previous=True, compares to prior window extremes (avoids lookahead bias).
    """
    close = data['close']
    roll_max = close.rolling(window, min_periods=window).max()
    roll_min = close.rolling(window, min_periods=window).min()
    if use_previous:
        thresh_max = roll_max.shift(1)
        thresh_min = roll_min.shift(1)
    else:
        thresh_max = roll_max
        thresh_min = roll_min
    breakout_up = close > thresh_max
    breakout_down = close < thresh_min
    return roll_max, roll_min, breakout_up, breakout_down


def _daily_open_and_last_from_df(data: pd.DataFrame, market_tz: str = "America/New_York"):
    """
    Helper: find today's first and last bar in MARKET_TZ using the DataFrame's DateTimeIndex.
    Returns (open_price, last_price, open_ts_local, last_ts_local) or (None, None, None, None).
    """
    if data.empty:
        return None, None, None, None

    # Ensure tz-aware UTC → convert to MARKET_TZ
    idx = data.index
    if idx.tz is None:
        data = data.tz_localize("UTC")
    data_local = data.tz_convert(market_tz)

    today = data_local.index[-1].date()
    day_slice = data_local[data_local.index.date == today]
    if day_slice.empty:
        return None, None, None, None

    open_ts_local = day_slice.index[0]
    last_ts_local = day_slice.index[-1]
    open_price = float(day_slice['close'].iloc[0])
    last_price = float(day_slice['close'].iloc[-1])
    return open_price, last_price, open_ts_local, last_ts_local


# ---------- Signal decision wrappers (normalized dicts; no DB writes here) ----------

def signal_macd_crossover(ticker: str, data: pd.DataFrame,
                          fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Action: BUY if MACD crosses above signal; SELL if crosses below; else NEUTRAL.
    signal_value = latest (MACD - signal)
    """
    macd_line, sig_line, _ = calculate_macd(data, fast, slow, signal)
    if len(macd_line) < 2:
        return None

    prev = macd_line.iloc[-2] - sig_line.iloc[-2]
    curr = macd_line.iloc[-1] - sig_line.iloc[-1]
    if pd.isna(prev) or pd.isna(curr):
        return None

    if (prev <= 0) and (curr > 0):
        action, strength = "BUY", "medium"
    elif (prev >= 0) and (curr < 0):
        action, strength = "SELL", "medium"
    else:
        action, strength = "NEUTRAL", "low"

    return {
        "ticker": ticker,
        "signal_type": "MACD",
        "action": action,
        "signal_value": float(curr),
        "confidence": None,
        "strength": strength,
        "params": {"fast": fast, "slow": slow, "signal": signal, "mode": "crossover"},
        "message": f"{ticker} MACD crossover → {action} (Δ={curr:.4f})"
    }


def signal_bollinger_mean_revert(ticker: str, data: pd.DataFrame, window: int = 20, k: float = 2.0):
    """
    Mean-reversion stance:
      close > upper_band ⇒ SELL
      close < lower_band ⇒ BUY
      else NEUTRAL
    signal_value = z-score distance from SMA20 (for logging)
    """
    sma, ub, lb = calculate_bollinger(data, window=window, k=k)
    close = data['close'].iloc[-1]
    sma_last, ub_last, lb_last = sma.iloc[-1], ub.iloc[-1], lb.iloc[-1]
    if pd.isna(sma_last) or pd.isna(ub_last) or pd.isna(lb_last):
        return None

    # z-score for value logging
    std = (ub_last - sma_last) / k if k != 0 else None
    z = (close - sma_last) / std if (std and std != 0) else None

    if close > ub_last:
        action, strength = "SELL", "medium"
    elif close < lb_last:
        action, strength = "BUY", "medium"
    else:
        action, strength = "NEUTRAL", "low"

    return {
        "ticker": ticker,
        "signal_type": "BOLLINGER",
        "action": action,
        "signal_value": None if z is None or pd.isna(z) else float(z),
        "confidence": None,
        "strength": strength,
        "params": {"window": window, "k": k, "posture": "mean_reversion"},
        "message": f"{ticker} Bollinger → {action} (close={close:.2f}, sma={sma_last:.2f})"
    }


def signal_ma_cross(ticker: str, data: pd.DataFrame, short: int = 50, long: int = 200):
    """
    Action: BUY on golden cross (short crosses above long), SELL on death cross.
    signal_value = (short_ma / long_ma) - 1 on the latest bar
    """
    short_ma, long_ma, cross_up, cross_down = calculate_ma_cross(data, short=short, long=long)
    sm, lm = short_ma.iloc[-1], long_ma.iloc[-1]
    if pd.isna(sm) or pd.isna(lm):
        return None

    ratio_minus_1 = (sm / lm) - 1 if lm != 0 else None

    if bool(cross_up.iloc[-1]):
        action, strength = "BUY", "high"
    elif bool(cross_down.iloc[-1]):
        action, strength = "SELL", "high"
    else:
        action, strength = "NEUTRAL", "low"

    return {
        "ticker": ticker,
        "signal_type": "MA_CROSS",
        "action": action,
        "signal_value": None if ratio_minus_1 is None or pd.isna(ratio_minus_1) else float(ratio_minus_1),
        "confidence": None,
        "strength": strength,
        "params": {"short": short, "long": long},
        "message": f"{ticker} MA({short}/{long}) → {action}"
    }


def signal_rsi_wilder(ticker: str, data: pd.DataFrame, period: int = 14,
                      overbought: float = 70.0, oversold: float = 30.0):
    """
    Action: SELL if RSI > overbought; BUY if RSI < oversold; else NEUTRAL.
    signal_value = latest RSI
    """
    rsi = calculate_rsi(data['close'], period=period)
    val = rsi.iloc[-1]
    if pd.isna(val):
        return None

    if val > overbought:
        action, strength = "SELL", "medium" if val < 80 else "high"
    elif val < oversold:
        action, strength = "BUY", "medium" if val > 20 else "high"
    else:
        action, strength = "NEUTRAL", "low"

    return {
        "ticker": ticker,
        "signal_type": "RSI",
        "action": action,
        "signal_value": float(val),
        "confidence": None,
        "strength": strength,
        "params": {"period": period, "overbought": overbought, "oversold": oversold, "smoothing": "Wilder"},
        "message": f"{ticker} RSI({period})={val:.2f} → {action}"
    }


def signal_sma_zscore(ticker: str, data: pd.DataFrame, window: int = 20, k: float = 2.0):
    """
    Normalized mean-reversion using z-score from SMA.
    Action: SELL if z >= +k; BUY if z <= -k; else NEUTRAL.
    signal_value = z
    """
    _, _, z = calculate_sma_zscore(data, window=window, ddof=0)
    val = z.iloc[-1]
    if pd.isna(val):
        return None

    if val >= +k:
        action, strength = "SELL", "medium"
    elif val <= -k:
        action, strength = "BUY", "medium"
    else:
        action, strength = "NEUTRAL", "low"

    return {
        "ticker": ticker,
        "signal_type": "SMA_Z",
        "action": action,
        "signal_value": float(val),
        "confidence": None,
        "strength": strength,
        "params": {"window": window, "k": k},
        "message": f"{ticker} SMA-Z({window})={val:.2f} → {action}"
    }


def signal_close_breakout(ticker: str, data: pd.DataFrame, window: int = 20, use_previous: bool = True):
    """
    Donchian-style close breakout without highs/lows.
    Action: BUY if close > prior rolling max_N; SELL if close < prior rolling min_N; else NEUTRAL.
    signal_value = 1 if breakout up, -1 if breakout down, 0 otherwise
    """
    roll_max, roll_min, brk_up, brk_dn = calculate_close_breakout(data, window=window, use_previous=use_previous)
    up = bool(brk_up.iloc[-1]) if len(brk_up) else False
    dn = bool(brk_dn.iloc[-1]) if len(brk_dn) else False

    if up:
        action, strength, val = "BUY", "high", 1.0
    elif dn:
        action, strength, val = "SELL", "high", -1.0
    else:
        action, strength, val = "NEUTRAL", "low", 0.0

    return {
        "ticker": ticker,
        "signal_type": "BREAKOUT",
        "action": action,
        "signal_value": val,
        "confidence": None,
        "strength": strength,
        "params": {"window": window, "use_previous": use_previous},
        "message": f"{ticker} Close breakout → {action}"
    }


def signal_daily_open_threshold(ticker: str, data: pd.DataFrame, pct: float = 0.03,
                                market_tz: str = "America/New_York"):
    """
    Percent move vs today's open in market time.
    Action: BUY if >= +pct; SELL if <= -pct; else NEUTRAL.
    signal_value = latest pct change
    """
    open_px, last_px, open_ts_local, last_ts_local = _daily_open_and_last_from_df(data, market_tz=market_tz)
    if open_px is None or open_px <= 0:
        return None
    pct_change = (last_px - open_px) / open_px

    if pct_change >= pct:
        action, strength = "BUY", "high" if pct_change >= 1.5 * pct else "medium"
    elif pct_change <= -pct:
        action, strength = "SELL", "high" if pct_change <= -1.5 * pct else "medium"
    else:
        action, strength = "NEUTRAL", "low"

    return {
        "ticker": ticker,
        "signal_type": "THRESHOLD",
        "action": action,
        "signal_value": float(pct_change),
        "confidence": None,
        "strength": strength,
        "params": {"basis": "daily_open", "threshold": pct, "market_tz": market_tz},
        "message": f"{ticker} {pct_change:.2%} vs daily open → {action}"
    }

# ---------- Signal generation ---------- #

def run_tickers_all(data):
    data = 
