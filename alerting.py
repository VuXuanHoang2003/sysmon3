from datetime import datetime
import os

os.makedirs("logs", exist_ok=True)

def log_alert(message):
    """
    Ghi cảnh báo ra file alerts.log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs/alerts.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] ALERT: {message}\n")
