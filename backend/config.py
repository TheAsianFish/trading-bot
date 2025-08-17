# config.py
import os

# --- DB ---
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "5432")

def _env_bool(name: str, default: bool = True) -> bool:
    return os.environ.get(name, str(default)).lower() in ("1", "true", "t", "yes", "y", "on")

# --- Alerts / Strategy knobs (read by signals engine) ---
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")  # env-only
ENABLE_ALERTS = _env_bool("ENABLE_ALERTS", True)
ALERT_COOLDOWN_MIN = int(os.environ.get("ALERT_COOLDOWN_MIN", "30"))

LOOKBACK_BARS = int(os.environ.get("LOOKBACK_BARS", "400"))          # covers 200-hr MA
MARKET_TZ = os.environ.get("MARKET_TZ", "America/New_York")
THRESHOLD_PCT = float(os.environ.get("THRESHOLD_PCT", "0.03"))
THRESHOLD_POSTURE = os.environ.get("THRESHOLD_POSTURE", "momentum").lower()  # or 'mean_reversion'

# Optional include-list like: "RSI,MACD,BOLLINGER"
INCLUDE_SIGNALS = [s.strip().upper() for s in os.environ.get("INCLUDE_SIGNALS", "").split(",") if s.strip()]

# Light regime filter (true = gate BUY/SELL if 50<200 for shorts / 50>200 for longs)
ENABLE_REGIME_FILTER = _env_bool("ENABLE_REGIME_FILTER", True)
