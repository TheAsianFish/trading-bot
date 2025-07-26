import os
from price_fetcher import fetch_and_store_all

def lambda_handler(event, context):
    print("=== Lambda Start ===")
    try:
        fetch_and_store_all()
        print("=== Lambda End: ALL OK ===")
        return {"status": "success"}
    except Exception as e:
        print("UNEXPECTED ERROR:", e)
        return {"error": str(e)}
