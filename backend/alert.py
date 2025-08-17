# alert.py
import requests

def send_alert(message: str, webhook_url: str, timeout: int = 5) -> bool:
    try:
        resp = requests.post(webhook_url, json={"content": message}, timeout=timeout)
        print(f"[alert-post] status={resp.status_code} body={resp.text[:180]}")
        return resp.status_code in (200, 204)
    except Exception as e:
        print(f"[alert-exc] {e.__class__.__name__}: {e}")
        return False
