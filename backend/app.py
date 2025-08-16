from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import pandas as pd
from datetime import datetime, timedelta, timezone

import config
from signals_engine import run_for_ticker  # unified orchestrator

app = Flask(__name__)
CORS(app)

def _conn():
    return psycopg2.connect(
        dbname=config.DB_NAME, user=config.DB_USER, password=config.DB_PASSWORD,
        host=config.DB_HOST, port=config.DB_PORT
    )

# --- helpers ---
def _parse_actions(s: str | None):
    if not s:
        return ["BUY", "SELL", "NEUTRAL"]
    vals = [v.strip().upper() for v in s.split(",") if v.strip()]
    return [v for v in vals if v in ("BUY", "SELL", "NEUTRAL")] or ["BUY", "SELL", "NEUTRAL"]

def _parse_since(s: str | None):
    if not s:  # default 7d
        return "7 days"
    s = s.strip().lower()
    if s.endswith("h"):
        return f"{int(s[:-1])} hours"
    if s.endswith("d"):
        return f"{int(s[:-1])} days"
    if s.endswith("m"):
        return f"{int(s[:-1])} minutes"
    return "7 days"

# --- health ---
@app.route("/health")
def health():
    return jsonify({"ok": True})

# --- prices (unchanged shape) ---
@app.route("/prices/<ticker>")
def price_history(ticker):
    try:
        range_param = request.args.get("range", default="All")
        now = datetime.now(timezone.utc)
        rng = {
            "24h": now - timedelta(days=1),
            "7d":  now - timedelta(days=7),
            "30d": now - timedelta(days=30),
            "90d": now - timedelta(days=90),
            "All": None
        }.get(range_param, None)

        with _conn() as conn, conn.cursor() as cur:
            if rng:
                cur.execute("""
                    SELECT timestamp, price
                    FROM prices
                    WHERE ticker=%s AND timestamp >= %s
                    ORDER BY timestamp ASC
                """, (ticker, rng))
            else:
                cur.execute("""
                    SELECT timestamp, price
                    FROM prices
                    WHERE ticker=%s
                    ORDER BY timestamp ASC
                """, (ticker,))
            rows = cur.fetchall()

        data = [{"timestamp": r[0].isoformat(), "price": float(r[1])} for r in rows]

        # lightweight decimation for long ranges
        if range_param in {"30d", "90d", "All"} and len(data) > 100:
            step = 4 if range_param == "30d" else 6
            data = data[::step]

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- signals: recent (all tickers) ---
@app.route("/signals/recent")
def signals_recent():
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
        actions = _parse_actions(request.args.get("actions"))
        since   = _parse_since(request.args.get("since"))

        with _conn() as conn:
            df = pd.read_sql("""
                SELECT timestamp, ticker, signal_type, action, signal_value, strength, message
                FROM signals
                WHERE action = ANY(%s) AND timestamp >= NOW() - (%s)::interval
                ORDER BY timestamp DESC
                LIMIT %s
            """, conn, params=(actions, since, limit))

        df["timestamp"] = df["timestamp"].apply(lambda t: t.isoformat())
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- signals: by ticker ---
@app.route("/signals/by/<ticker>")
def signals_by_ticker(ticker):
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
        actions = _parse_actions(request.args.get("actions"))
        since   = _parse_since(request.args.get("since"))

        with _conn() as conn:
            df = pd.read_sql("""
                SELECT timestamp, signal_type, action, signal_value, strength, message
                FROM signals
                WHERE ticker = %s AND action = ANY(%s)
                  AND timestamp >= NOW() - (%s)::interval
                ORDER BY timestamp DESC
                LIMIT %s
            """, conn, params=(ticker, actions, since, limit))

        df["timestamp"] = df["timestamp"].apply(lambda t: t.isoformat())
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- signals: summary ---
@app.route("/signals/summary")
def signals_summary():
    try:
        group_by = request.args.get("group_by", "signal_type").lower()
        since    = _parse_since(request.args.get("since"))

        if group_by == "action":
            sql = """
              SELECT action, COUNT(*) AS count
              FROM signals
              WHERE timestamp >= NOW() - (%s)::interval
              GROUP BY action
              ORDER BY count DESC
            """
            key = "action"
        else:
            sql = """
              SELECT signal_type AS type, COUNT(*) AS count
              FROM signals
              WHERE timestamp >= NOW() - (%s)::interval
              GROUP BY signal_type
              ORDER BY count DESC
            """
            key = "type"

        with _conn() as conn:
            df = pd.read_sql(sql, conn, params=(since,))

        # normalize keys so existing charts work (type/count or action/count)
        return jsonify([{key: row[key], "count": int(row["count"])} for _, row in df.iterrows()])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- manual trigger (button) ---
@app.route("/signals/generate/<ticker>", methods=["POST"])
def signals_generate(ticker):
    try:
        summary = run_for_ticker(ticker, triggered_by="manual")
        return jsonify({"status": "ok", **summary})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # For local dev only; EB will run via gunicorn
    app.run(host="0.0.0.0", port=5000, debug=True)
