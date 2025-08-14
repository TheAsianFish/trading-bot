# alert.py
import os
import requests
from typing import Optional

DEFAULT_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

def send_alert(message: str,
               webhook_url: Optional[str] = None,
               timeout_sec: int = 5) -> bool:
    """
    Send a simple Discord webhook message.
    Returns True on success (HTTP 200/204), False otherwise.
    """
    url = webhook_url or DEFAULT_WEBHOOK
    if not url:
        print("send_alert: No webhook URL provided and DISCORD_WEBHOOK_URL not set.")
        return False

    try:
        resp = requests.post(url, json={"content": message}, timeout=timeout_sec)
        if resp.status_code in (200, 204):
            print("Alert sent to Discord")
            return True
        print(f"Discord webhook error: {resp.status_code} {resp.text[:200]}")
        return False
    except Exception as e:
        print("Failed to send Discord alert:", e)
        return False
