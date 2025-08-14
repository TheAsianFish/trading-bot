import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

import pandas as pd
import psycopg2

from plot_prices import fetch_price_history
from db_insert import insert_signal
from alert import send_alert
import config

# ====== ENV / CONSTANTS ======
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")                 # Discord webhook (optional)
ENABLE_ALERTS = os.getenv("ENABLE_ALERTS", "true").lower() in ("1", "true", "yes", "y")
ALERT_COOLDOWN_MIN = int(os.getenv("ALERT_COOLDOWN_MIN", "30"))  # minutes

LOOKBACK_BARS = int(os.getenv("LOOKBACK_BARS", "400"))           # covers MA(200) on hourly
MARKET_TZ = os.getenv("MARKET_TZ", "America/New_York")

THRESHOLD_PCT = float(os.getenv("THRESHOLD_PCT", "0.03"))        # 3% default
THRESHOLD_POSTURE = os.getenv("THRESHOLD_POSTURE", "momentum").lower()  # 'momentum' | 'mean_reversion'

# If you want to toggle modules from env (comma-separated list), leave empty to use defaults below.
INCLUDE_SIGNALS = [s.strip().upper() for s in os.getenv("INCLUDE_SIGNALS", "").split(",") if s.strip()]


# ====== BACKCOMPAT ADAPTER (if legacy callsites still use it) ======
def insert_generated_signal(
    ticker: str,
    signal_type: str,
    timestamp,
    signal_value,
    signal_strength,          # 'BUY' | 'SELL' | 'NEUTRAL'
    *,
    triggered_by: str = "manual",
    params: Optional[dict] = None,
    message: Optional[str] = None,
    confidence: Optional[float] = None,
    strength: Optional[str] = None
):
    """
    Back-compat adapter that writes to unified `signals` table.
    """
    action = signal_strength if signal_strength in ("BUY", "SELL") else "NEUTRAL"
    final_strength = strength or ("high" if action in ("BUY", "SELL") else "low")
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
        timestamp=timestamp,
        strategy=None,
    )


# ====== CORE INDICATOR CALCS (vectorized) ======
def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    close = data['close']
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist

def calculate_bollinger(data: pd.DataFrame, window: int = 20, k: float = 2.0):
    close = data['close']
    sma = close.rolling(window, min_periods=window).mean()
    std = close.rolling(window, min_periods=window).std(ddof=0)
    upper_band = sma + k * std
    lower_band = sma - k * std
    return sma, upper_band, lower_band

def calculate_ma_cross(data: pd.DataFrame, short: int = 50, long: int = 200):
    close = data['close']
    short_ma = close.rolling(short, min_periods=short).mean()
    long_ma  = close.rolling(long,  min_periods=long).mean()
    prev_above = short_ma.shift(1) > long_ma.shift(1)
    curr_above = short_ma > long_ma
    cross_up   = (~prev_above) & curr_above
    cross_down = prev_above & (~curr_above)
    return short_ma, long_ma, cross_up, cross_down

def calculate_rsi(close: pd.Series, period: int = 14):
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Extras
def calculate_sma_zscore(data: pd.DataFrame, window: int = 20, ddof: int = 0):
    close = data['close']
    sma = close.rolling(window, min_periods=window).mean()
    std = close.rolling(window, min_periods=window).std(ddof=ddof)
    z = (close - sma) / std
    return sma, std, z

def calculate_close_breakout(data: pd.DataFrame, window: int = 20, use_previous: bool = True):
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

def _daily_open_and_last_from_df(data: pd.DataFrame, market_tz: str = MARKET_TZ):
    """
    Find today's first and last bar in market time.
    Returns (open_price, last_price) or (None, None) if not available.
    """
    if data.empty:
        return None, None
    if data.index.tz is None:
        data = data.tz_localize("UTC")
    data_local = data.tz_convert(market_tz)
    today = data_local.index[-1].date()
    day_slice = data_local[data_local.index.date == today]
    if day_slice.empty:
        return None, None
    open_price = float(day_slice['close'].iloc[0])
    last_price = float(day_slice['close'].iloc[-1])
    return open_price, last_price


# ====== SIGNAL DECISION WRAPPERS (pure; no DB/alerts) ======
def signal_macd_crossover(ticker: str, data: pd.DataFrame,
                          fast: int = 12, slow: int = 26, signal: int = 9):
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
        "strategy": f"MACD_{fast}_{slow}_{signal}_xover",
        "action": action,
        "signal_value": float(curr),
        "confidence": None,
        "strength": strength,
        "params": {"fast": fast, "slow": slow, "signal": signal, "mode": "crossover"},
        "message": f"{ticker} MACD crossover → {action} (Δ={curr:.4f})"
    }

def signal_bollinger_mean_revert(ticker: str, data: pd.DataFrame, window: int = 20, k: float = 2.0):
    sma, ub, lb = calculate_bollinger(data, window=window, k=k)
    close = data['close'].iloc[-1]
    sma_last, ub_last, lb_last = sma.iloc[-1], ub.iloc[-1], lb.iloc[-1]
    if pd.isna(sma_last) or pd.isna(ub_last) or pd.isna(lb_last):
        return None
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
        "strategy": f"BOLL_{window}_{k}_mr",
        "action": action,
        "signal_value": None if z is None or pd.isna(z) else float(z),
        "confidence": None,
        "strength": strength,
        "params": {"window": window, "k": k, "posture": "mean_reversion"},
        "message": f"{ticker} Bollinger → {action} (close={close:.2f}, sma={sma_last:.2f})"
    }

def signal_ma_cross(ticker: str, data: pd.DataFrame, short: int = 50, long: int = 200):
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
        "strategy": f"MA_{short}_{long}",
        "action": action,
        "signal_value": None if ratio_minus_1 is None or pd.isna(ratio_minus_1) else float(ratio_minus_1),
        "confidence": None,
        "strength": strength,
        "params": {"short": short, "long": long},
        "message": f"{ticker} MA({short}/{long}) → {action}"
    }

def signal_rsi_wilder(ticker: str, data: pd.DataFrame, period: int = 14,
                      overbought: float = 70.0, oversold: float = 30.0):
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
        "strategy": f"RSI_{period}_{int(overbought)}_{int(oversold)}",
        "action": action,
        "signal_value": float(val),
        "confidence": None,
        "strength": strength,
        "params": {"period": period, "overbought": overbought, "oversold": oversold, "smoothing": "Wilder"},
        "message": f"{ticker} RSI({period})={val:.2f} → {action}"
    }

def signal_close_breakout(ticker: str, data: pd.DataFrame, window: int = 20, use_previous: bool = True):
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
        "strategy": f"BRK_{window}_{'prev' if use_previous else 'curr'}",
        "action": action,
        "signal_value": val,
        "confidence": None,
        "strength": strength,
        "params": {"window": window, "use_previous": use_previous},
        "message": f"{ticker} Close breakout → {action}"
    }

def signal_daily_open_threshold(ticker: str, data: pd.DataFrame,
                                pct: float = THRESHOLD_PCT,
                                market_tz: str = MARKET_TZ,
                                posture: str = THRESHOLD_POSTURE):
    """
    Percent move vs today's open. Posture:
      - 'momentum': BUY if pct_change >= +pct; SELL if <= -pct
      - 'mean_reversion': SELL if pct_change >= +pct; BUY if <= -pct
    """
    open_px, last_px = _daily_open_and_last_from_df(data, market_tz=market_tz)
    if open_px is None or open_px <= 0:
        return None
    pct_change = (last_px - open_px) / open_px

    if posture == "mean_reversion":
        if pct_change >= pct:
            action, strength = "SELL", "high" if pct_change >= 1.5 * pct else "medium"
        elif pct_change <= -pct:
            action, strength = "BUY", "high" if pct_change <= -1.5 * pct else "medium"
        else:
            action, strength = "NEUTRAL", "low"
        strat = f"THRESH_OPEN_{int(pct*1000)/10}_MR"
    else:  # momentum (default)
        if pct_change >= pct:
            action, strength = "BUY", "high" if pct_change >= 1.5 * pct else "medium"
        elif pct_change <= -pct:
            action, strength = "SELL", "high" if pct_change <= -1.5 * pct else "medium"
        else:
            action, strength = "NEUTRAL", "low"
        strat = f"THRESH_OPEN_{int(pct*1000)/10}_MOM"

    return {
        "ticker": ticker,
        "signal_type": "THRESHOLD",
        "strategy": strat,
        "action": action,
        "signal_value": float(pct_change),
        "confidence": None,
        "strength": strength,
        "params": {"basis": "daily_open", "threshold": pct, "market_tz": market_tz, "posture": posture},
        "message": f"{ticker} {pct_change:.2%} vs daily open → {action}"
    }


# ====== EMIT / ALERT HELPERS ======
def _emit(payload: Dict[str, Any], *,
          triggered_by: str = "manual",
          timestamp: Optional[datetime] = None) -> bool:
    """
    Centralized DB write to unified `signals` table.
    """
    try:
        insert_signal(
            ticker=payload["ticker"],
            signal_type=payload["signal_type"],
            strategy=payload.get("strategy"),
            action=payload["action"],
            signal_value=payload.get("signal_value"),
            confidence=payload.get("confidence"),
            strength=payload.get("strength"),
            params=payload.get("params"),
            triggered_by=triggered_by,
            message=payload.get("message"),
            timestamp=timestamp,  # bar timestamp (UTC); if None, DB NOW()
        )
        return True
    except Exception as e:
        print(f"_emit insert failed: {e}")
        return False

def _last_similar_signal_time(ticker: str, signal_type: str, action: str) -> Optional[datetime]:
    """
    Return timestamp of the most recent (ticker, signal_type, action) in `signals`.
    """
    conn = cur = None
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD,
            host=config.DB_HOST, port=config.DB_PORT
        )
        cur = conn.cursor()
        cur.execute(
            """
            SELECT timestamp
            FROM signals
            WHERE ticker = %s AND signal_type = %s AND action = %s
            ORDER BY timestamp DESC
            LIMIT 1;
            """,
            (ticker, signal_type, action)
        )
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"_last_similar_signal_time error: {e}")
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()

def _should_alert(ticker: str, signal_type: str, action: str,
                  cooldown_min: int = ALERT_COOLDOWN_MIN) -> bool:
    """
    True if no identical alert within cooldown window.
    """
    ts = _last_similar_signal_time(ticker, signal_type, action)
    if not ts:
        return True
    return (datetime.now(timezone.utc) - ts) >= timedelta(minutes=cooldown_min)


# ====== DATA LOADER (hourly bars) ======
def _load_prices(ticker: str, lookback_bars: int = LOOKBACK_BARS) -> Optional[pd.DataFrame]:
    """
    Load recent bars for `ticker` from DB and return a clean DataFrame:
      - index: tz-aware UTC timestamps, ascending
      - columns: ['close'] (float)
    Trims to last `lookback_bars` for efficiency.
    """
    df = fetch_price_history(ticker)  # expects columns: ['timestamp', 'price']
    if df is None or df.empty:
        return None

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp")
    df["close"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["close"])
    df = df.set_index("timestamp")[["close"]]

    if lookback_bars and lookback_bars > 0:
        df = df.tail(lookback_bars)

    return df if not df.empty else None


# ====== ORCHESTRATORS ======
def run_for_ticker(ticker: str, *, triggered_by: str = "manual") -> Dict[str, Any]:
    """
    Load recent hourly bars, run enabled signals, write to unified `signals` table,
    and send Discord alerts (BUY/SELL) with DB-backed cooldown if enabled.
    Returns a compact summary.
    """
    data = _load_prices(ticker, lookback_bars=LOOKBACK_BARS)
    if data is None:
        return {"ticker": ticker, "emitted": 0, "errors": ["no_data"]}

    bar_ts: Optional[datetime] = data.index[-1].to_pydatetime() if len(data.index) else None

    # Registry of signal modules (kept small & solid). Toggle with INCLUDE_SIGNALS if set.
    registry: List[tuple] = [
        ("THRESHOLD", signal_daily_open_threshold, {"pct": THRESHOLD_PCT, "market_tz": MARKET_TZ, "posture": THRESHOLD_POSTURE}),
        ("MACD",      signal_macd_crossover,       {}),
        ("RSI",       signal_rsi_wilder,           {"period": 14, "overbought": 70.0, "oversold": 30.0}),
        ("MA_CROSS",  signal_ma_cross,             {"short": 50, "long": 200}),
        ("BOLLINGER", signal_bollinger_mean_revert,{"window": 20, "k": 2.0}),
        # Optional, enable later if desired:
        # ("BREAKOUT",  signal_close_breakout,       {"window": 20, "use_previous": True}),
        # ("SMA_Z",     signal_sma_zscore,          {"window": 20, "k": 2.0}),
    ]
    if INCLUDE_SIGNALS:
        allowed = set(INCLUDE_SIGNALS)
        registry = [m for m in registry if m[0] in allowed]

    emitted: List[Dict[str, Any]] = []
    errors: List[str] = []

    for name, fn, kwargs in registry:
        try:
            payload = fn(ticker, data, **kwargs)
        except Exception as e:
            errors.append(f"{name}:{e}")
            continue
        if not payload:
            continue

        # Decide if we will alert (check BEFORE insert so we don't see the row we are about to write)
        will_alert = (
            ENABLE_ALERTS
            and WEBHOOK_URL
            and payload["action"] in ("BUY", "SELL")
            and _should_alert(payload["ticker"], payload["signal_type"], payload["action"])
        )

        # Insert first; only alert if insert succeeds
        if _emit(payload, triggered_by=triggered_by, timestamp=bar_ts):
            emitted.append(payload)
            if will_alert:
                try:
                    send_alert(payload.get("message") or f'{payload["ticker"]} {payload["signal_type"]} → {payload["action"]}',
                               WEBHOOK_URL)
                except Exception as e:
                    errors.append(f"alert:{name}:{e}")
        else:
            errors.append(f"emit:{name}")

    return {
        "ticker": ticker,
        "emitted": len(emitted),
        "last_actions": {p["signal_type"]: p["action"] for p in emitted},
        "errors": errors
    }

def run_for_all_tickers(tickers: List[str], *, triggered_by: str = "auto") -> Dict[str, Any]:
    summary: Dict[str, Any] = {"total_emitted": 0, "per_ticker": {}, "errors": {}}
    for t in tickers:
        res = run_for_ticker(t, triggered_by=triggered_by)
