from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import config
import pandas as pd
from signals_engine import(
    generate_rsi_signal, generate_macd_signal, generate_bollinger_signal, generate_volume_signal
)

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

        #Convert result to JSON format
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
        conn = get_db_connection()
        cur = conn.cursor()
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

@app.route("/signals/generate/<ticker>", methods=["POST"])
def generate_signals(ticker):
    try:

        generate_rsi_signal(ticker)
        generate_macd_signal(ticker)
        generate_bollinger_signal(ticker)
        generate_volume_signal(ticker)

        return jsonify({"status": f"RSI and MACD signals generated for {ticker}"})
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