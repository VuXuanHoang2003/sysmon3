import time
import joblib
from log_parser import parse_log_file
from alerting import log_alert
from telegram_alert import send_telegram_alert

# Load model và đặc trưng
model = joblib.load("model/model.pkl")
feature_columns = joblib.load("model/feature_columns.pkl")

# Ngưỡng phát hiện bất thường (có thể điều chỉnh)
THRESHOLD = -0.05  # thấp hơn → nhạy hơn → tăng Recall

def build_alert_message(row):
    """
    Tạo nội dung cảnh báo ngắn gọn
    """
    reasons = []
    if row["is_failed_login"]:
        reasons.append("Failed login")
    if row["is_admin_path"]:
        reasons.append("Admin path access")
    if row["is_root_access"]:
        reasons.append("Root access")
    if row["is_web"]:
        reasons.append("Suspicious web request")

    reason_text = ", ".join(reasons) if reasons else "General anomaly"
    return f"Anomaly detected | Reasons: {reason_text}"

def detect_and_alert():
    """
    Phát hiện bất thường và gửi cảnh báo
    """
    df = parse_log_file("data/test_logs.log")
    X = df[feature_columns]

    df["score"] = model.decision_function(X)
    df["prediction"] = df["score"].apply(lambda x: -1 if x < THRESHOLD else 1)

    alerts = df[df["prediction"] == -1]

    for _, row in alerts.iterrows():
        msg = build_alert_message(row)
        log_alert(msg)
        send_telegram_alert(msg)

    print(f"🔎 Quét xong: {len(alerts)} bất thường được phát hiện.")

if __name__ == "__main__":
    print("🚀 Hệ thống phát hiện bất thường đang chạy...")
    while True:
        detect_and_alert()
        time.sleep(30)  # chờ 30 giây rồi quét tiếp
