from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import config
import pandas as pd
from datetime import datetime, timedelta
from signals_engine import generate_signals

app = Flask(__name__)
CORS(app)

#Connect to PostgreSQL DB
def get_db_connection():
    return psycopg2.connect(
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT
    )

#Get the 10 most recent signals
@app.route("/signals/recent")
def recent_signals():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, ticker, type, price
            FROM signals
            ORDER BY timestamp DESC
            LIMIT 10;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        data = [
            {"timestamp": str(r[0]), "ticker": r[1], "type": r[2], "price": float(r[3])}
            for r in rows
        ]
        return jsonify(data)
    
    except Exception as e:
        return jsonify({"error": str(e)})

#Get price history for a specific ticker 
@app.route("/prices/<ticker>")
def price_history(ticker):
    try:
        range_param = request.args.get("range", default="All")

        now = datetime.utcnow()
        range_map = {
            "24h": now - timedelta(days=1),
            "7d": now - timedelta(days=7),
            "30d": now - timedelta(days=30),
            "90d": now - timedelta(days=90),
            "All": None
        }
        threshold = range_map.get(range_param, None)

        conn = get_db_connection()
        cur = conn.cursor()

        if threshold:
            cur.execute("""
                SELECT timestamp, price
                FROM prices
                WHERE ticker = %s AND timestamp >= %s
                ORDER BY timestamp ASC;
            """, (ticker, threshold))
        else:
            cur.execute("""
                SELECT timestamp, price
                FROM prices
                WHERE ticker = %s
                ORDER BY timestamp ASC;
            """, (ticker,))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        data = [
            {"timestamp": str(r[0]), "price": float(r[1])}
            for r in rows
        ]

        if range_param in ["30d", "90d", "All"] and len(data) > 100:
            step = 4 if range_param == "30d" else 6
            data = data[::step]

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)})

#Summary of signal counts by type
@app.route("/signals/summary")
def signal_summary():
    try:
        conn = get_db_connection()
        df = pd.read_sql("""
            SELECT type, COUNT(*) as count
            FROM signals
            GROUP BY type;
        """, conn)
        conn.close()

        return jsonify(df.to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)})

# Corrected signal generator route
@app.route("/signals/generate/<ticker>", methods=["POST"])
def generate_signals_route(ticker):
    try:
        generate_signals(ticker)
        return jsonify({"status": f"Signals generated for {ticker}"})
    except Exception as e:
        return jsonify({"error": str(e)})

# Endpoint to view recent generated signals for a ticker
@app.route("/signals/generated/<ticker>", methods=["GET"])
def get_generated_signals(ticker):
    try:
        conn = get_db_connection()
        query = """
            SELECT timestamp, signal_type, signal_value, signal_strength
            FROM generated_signals
            WHERE ticker = %s
            ORDER BY timestamp DESC
            LIMIT 20;
        """
        df = pd.read_sql(query, conn, params=(ticker,))
        conn.close()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)})

#Run the Flask server locally
if __name__ == "__main__":
    app.run(debug=True)