import requests
from datetime import datetime, timezone
import time
import os
import json

LOKI_URL = "http://100.31.144.126:3100"
STATE_FILE = "data/last_timestamp.json"
LOG_FILE = "data/logs.log"
REAL_TIME_INTERVAL = 10  # Thời gian quét (giây) - giảm xuống 10 giây để real-time hơn

def load_last_timestamp():
    """Đọc timestamp cuối cùng đã lấy log"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                return data.get("last_timestamp")
        except:
            pass
    return None

def save_last_timestamp(timestamp):
    """Lưu timestamp cuối cùng đã lấy log"""
    with open(STATE_FILE, "w") as f:
        json.dump({"last_timestamp": timestamp}, f)

def get_log():
    """Lấy log theo thời gian thực từ Loki"""
    # Tạo thư mục data nếu chưa tồn tại    
    os.makedirs("data", exist_ok=True)
    
    # Thời điểm hiện tại (UTC) - nanoseconds
    end = int(datetime.now(timezone.utc).timestamp() * 1_000_000_000)
    
    # Lấy timestamp cuối cùng hoặc lấy log từ 5 phút trước
    last_ts = load_last_timestamp()
    if last_ts:
        start = last_ts + 1  # Bắt đầu từ log tiếp theo
    else:
        # Lần đầu tiên, lấy log từ 5 phút trước
        start = end - (5 * 60 * 1_000_000_000)
    
    params = {
        "query": '{job="nginx"}',
        "start": start,
        "end": end,
        "limit": 5000  # Tăng limit để không bỏ sót log
    }
    
    try:
        resp = requests.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params=params,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        
        new_logs = []
        max_timestamp = start
        
        # Thu thập tất cả log mới
        for stream in data.get("data", {}).get("result", []):
            for ts, line in stream.get("values", []):
                timestamp_ns = int(ts)
                new_logs.append((timestamp_ns, line))
                max_timestamp = max(max_timestamp, timestamp_ns)
        
        # Sắp xếp theo timestamp
        new_logs.sort(key=lambda x: x[0])
        
        # Ghi log mới vào file (append mode để real-time)
        if new_logs:
            mode = "a" if last_ts else "w"  # Append nếu đã có, write nếu lần đầu
            with open(LOG_FILE, mode, encoding="utf-8") as f:
                for ts, line in new_logs:
                    print(f"[{datetime.fromtimestamp(ts/1e9).strftime('%H:%M:%S')}] {line}")
                    f.write(line + "\n")
            
            # Lưu timestamp cuối cùng
            save_last_timestamp(max_timestamp)
            print(f"✅ Thu thập được {len(new_logs)} log mới")
        else:
            print("⏳ Không có log mới")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi kết nối Loki: {e}")
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")

def rotate_log_file(max_size_mb=10):
    """Xoay vòng file log nếu quá lớn"""
    if os.path.exists(LOG_FILE):
        size_mb = os.path.getsize(LOG_FILE) / (1024 * 1024)
        if size_mb > max_size_mb:
            backup_file = f"data/logs_backup_{int(time.time())}.log"
            os.rename(LOG_FILE, backup_file)
            print(f"📦 Đã backup log cũ: {backup_file}")
                    
if __name__ == "__main__":
    print("🚀 Hệ thống lấy log theo thời gian thực đang chạy...")
    print(f"⏱️  Quét log mỗi {REAL_TIME_INTERVAL} giây")
    print(f"📡 Kết nối Loki: {LOKI_URL}")
    print("-" * 60)
    
    while True:
        try:
            rotate_log_file()  # Kiểm tra và xoay vòng log nếu cần
            get_log()
            time.sleep(REAL_TIME_INTERVAL)
        except KeyboardInterrupt:
            print("\n🛑 Dừng hệ thống...")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            time.sleep(REAL_TIME_INTERVAL)