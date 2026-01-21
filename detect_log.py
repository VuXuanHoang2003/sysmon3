import time
import joblib
import pandas as pd
import re
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict, deque
from log_parser import parse_log_file
from alerting import log_alert
from telegram_alert import send_telegram_alert

# Load model và đặc trưng
try:
    model = joblib.load("model/model.pkl")
    feature_columns = joblib.load("model/feature_columns.pkl")
    MODEL_LOADED = True
except:
    print("⚠️  Không tìm thấy model, chỉ sử dụng rule-based detection")
    MODEL_LOADED = False

# Cấu hình
THRESHOLD = 0.02
FLOOD_THRESHOLD = 10   # số request
TIME_WINDOW = 60       # giây
DETECT_INTERVAL = 10   # Thời gian quét (giây) - real-time hơn

# Tracking state
processed_lines = 0
ip_request_tracker = defaultdict(lambda: deque(maxlen=1000))  # Theo dõi request theo IP

def extract_fields_from_log(line):
    """
    Tách IP, URI, timestamp, status code từ dòng log nginx
    """
    ip_match = re.match(r"(\d+\.\d+\.\d+\.\d+)", line)
    uri_match = re.search(r"\"[A-Z]+\s+([^ ]+)", line)
    time_match = re.search(r"\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})", line)
    status_match = re.search(r'"\s+(\d{3})\s+', line)
    method_match = re.search(r'"([A-Z]+)\s+', line)
    
    ip = ip_match.group(1) if ip_match else "unknown"
    uri = uri_match.group(1) if uri_match else "unknown"
    status = status_match.group(1) if status_match else "000"
    method = method_match.group(1) if method_match else "GET"
    
    if time_match:
        try:
            timestamp = datetime.strptime(time_match.group(1), "%d/%b/%Y:%H:%M:%S")
        except:
            timestamp = datetime.now()
    else:
        timestamp = datetime.now()
    
    return ip, uri, timestamp, status, method

def detect_suspicious_patterns(ip, uri, status, method):
    """
    Phát hiện các pattern đáng ngờ
    """
    alerts = []
    
    # SQL Injection patterns
    sql_patterns = [r"union.*select", r"or\s+1\s*=\s*1", r"'\s*or\s*'", 
                    r"drop\s+table", r"insert\s+into", r"--", r";", r"xp_"]
    for pattern in sql_patterns:
        if re.search(pattern, uri, re.IGNORECASE):
            alerts.append(f"SQL Injection attempt")
            break
    
    # XSS patterns
    xss_patterns = [r"<script", r"javascript:", r"onerror\s*=", r"onload\s*="]
    for pattern in xss_patterns:
        if re.search(pattern, uri, re.IGNORECASE):
            alerts.append(f"XSS attempt")
            break
    
    # Path traversal
    if re.search(r"\.\./|\.\.\\\\|\.\./\.\./", uri):
        alerts.append(f"Path traversal attempt")
    
    # Admin panel scanning
    admin_paths = [r"/admin", r"/wp-admin", r"/phpmyadmin", r"/config", r"/console"]
    for pattern in admin_paths:
        if re.search(pattern, uri, re.IGNORECASE):
            alerts.append(f"Admin panel scanning")
            break
    
    # 401/403 errors (unauthorized access)
    if status in ["401", "403"]:
        alerts.append(f"Unauthorized access attempt (Status: {status})")
    
    # 500 errors (potential exploitation)
    if status in ["500", "502", "503"]:
        alerts.append(f"Server error triggered (Status: {status})")
    
    return alerts

def detect_http_flood_realtime(records_df):
    """
    Phát hiện HTTP flood theo thời gian thực
    """
    if records_df.empty:
        return pd.DataFrame()
    
    alerts = []
    now = datetime.now()
    
    for (ip, uri), group in records_df.groupby(["ip", "uri"]):
        group = group.sort_values("timestamp")
        times = group["timestamp"].values
        
        # Kiểm tra trong cửa sổ thời gian
        for i in range(len(times)):
            start = times[i]
            end = start + pd.Timedelta(seconds=TIME_WINDOW)
            count = ((times >= start) & (times <= end)).sum()
            
            if count >= FLOOD_THRESHOLD:
                row_data = group.iloc[i].to_dict()
                row_data["count"] = count
                alerts.append(row_data)
                break
    
    return pd.DataFrame(alerts)

def process_new_logs():
    """
    Xử lý log mới (incremental)
    """
    global processed_lines
    
    log_file = "data/logs.log"
    if not os.path.exists(log_file):
        print("⏳ Chờ file log...")
        return
    
    records = []
    suspicious_alerts = []
    
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        # Bỏ qua các dòng đã xử lý
        for _ in range(processed_lines):
            if not f.readline():
                break
        
        # Xử lý các dòng mới
        new_line_count = 0
        for line in f:
            new_line_count += 1
            ip, uri, timestamp, status, method = extract_fields_from_log(line)
            
            records.append({
                "ip": ip,
                "uri": uri,
                "timestamp": timestamp,
                "status": status,
                "method": method,
                "raw_log": line.strip()
            })
            
            # Phát hiện pattern đáng ngờ ngay lập tức
            patterns = detect_suspicious_patterns(ip, uri, status, method)
            for pattern in patterns:
                suspicious_alerts.append({
                    "ip": ip,
                    "uri": uri,
                    "pattern": pattern,
                    "status": status,
                    "timestamp": timestamp
                })
        
        processed_lines += new_line_count
    
    if not records:
        print("⏳ Không có log mới để phân tích")
        return
    
    print(f"📊 Phân tích {len(records)} log mới (Tổng: {processed_lines} dòng)")
    
    df = pd.DataFrame(records)
    
    # 1. Phát hiện suspicious patterns
    if suspicious_alerts:
        for alert in suspicious_alerts:
            msg = f"🚨 {alert['pattern']} | IP: {alert['ip']} | URI: {alert['uri'][:50]} | Status: {alert['status']}"
            print(msg)
            log_alert(msg)
            send_telegram_alert(msg)
        print(f"⚠️  Phát hiện {len(suspicious_alerts)} pattern đáng ngờ")
    
    # 2. Phát hiện HTTP flood
    flood_alerts = detect_http_flood_realtime(df)
    if not flood_alerts.empty:
        for _, row in flood_alerts.iterrows():
            msg = f"🚨 HTTP Flood detected | IP: {row['ip']} | URI: {row['uri'][:50]} | Count: {row['count']} requests/{TIME_WINDOW}s"
            print(msg)
            log_alert(msg)
            send_telegram_alert(msg)
        print(f"🔥 Phát hiện {len(flood_alerts)} HTTP flood attack")
    
    if not suspicious_alerts and flood_alerts.empty:
        print("✅ Không phát hiện mối đe dọa")

def detect_and_alert():
    """Main detection loop"""
    try:
        process_new_logs()
    except Exception as e:
        print(f"❌ Lỗi khi phân tích: {e}")

if __name__ == "__main__":
    print("🚀 Hệ thống phát hiện tấn công theo thời gian thực đang chạy...")
    print(f"⏱️  Quét log mỗi {DETECT_INTERVAL} giây")
    print(f"🔥 HTTP Flood threshold: {FLOOD_THRESHOLD} requests/{TIME_WINDOW}s")
    print("-" * 60)
    
    while True:
        try:
            detect_and_alert()
            time.sleep(DETECT_INTERVAL)
        except KeyboardInterrupt:
            print("\n🛑 Dừng hệ thống...")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            time.sleep(DETECT_INTERVAL)
