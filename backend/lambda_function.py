# lambda_function.py
import os
from price_fetcher import fetch_and_store_all
from signals_engine import run_for_all_tickers  # orchestrator inserts signals (+ alerts if enabled)

_DEFAULT_TICKERS = "AAPL,MSFT,GOOGL,TSLA,^GSPC,BTC-USD,ETH-USD"
TICKERS = [t.strip() for t in os.getenv("TICKERS", _DEFAULT_TICKERS).split(",") if t.strip()]

def lambda_handler(event, context):
    print("=== Lambda Start ===")
    try:
        # 1) Ingest latest bars into `prices`
        fetch_and_store_all()

        # 2) Generate ALL signals (and send alerts if enabled env is set)
        summary = run_for_all_tickers(TICKERS, triggered_by="auto")

        print("=== Lambda End: ALL OK ===")
        # Compact response for CloudWatch/observability
        per_ticker_counts = {k: v.get("emitted", 0) for k, v in summary.get("per_ticker", {}).items()}
        return {
            "status": "success",
            "total_emitted": summary.get("total_emitted", 0),
            "per_ticker": per_ticker_counts,
            "errors": summary.get("errors", {})
        }
    except Exception as e:
        print("UNEXPECTED ERROR:", e)
        return {"status": "error", "message": str(e)}
