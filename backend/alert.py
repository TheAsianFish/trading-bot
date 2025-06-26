# alert.py
import requests

def send_alert(message, webhook_url):
    data = {"content": message}
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            print("Alert sent to Discord")
        else:
            print(f"Discord webhook error: {response.status_code}")
    except Exception as e:
        print("Failed to send Discord alert:", e)

