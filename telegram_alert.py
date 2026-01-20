import requests

# Thay bằng token và chat ID của bạn
#TELEGRAM_BOT_TOKEN = "8265124429:AAFpgyshrcXM6lgjJX4blfKeIuyVPOoba7Y"
TELEGRAM_BOT_TOKEN ="8085018395:AAGUzaYYcYyczL-CyfVuIbPQyPr0poife0Y"
#TELEGRAM_CHAT_ID = "8593741640"
TELEGRAM_CHAT_ID = "2128506962"

def send_telegram_alert(message):
    """
    Gửi cảnh báo ngắn gọn qua Telegram
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"AI ALERT: {message}"
    }
    requests.post(url, data=payload)
