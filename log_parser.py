import re
import pandas as pd

def parse_log_file(file_path):
    """
    Đọc file log và trích xuất đặc trưng cho từng dòng log.
    Trả về DataFrame để đưa vào mô hình.
    """
    records = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            record = {
                "is_failed_login": 1 if "Failed password" in line or "Invalid user" in line else 0,
                "is_success_login": 1 if "Accepted password" in line or "Accepted publickey" in line else 0,
                "is_root_access": 1 if "sudo" in line or "USER=root" in line else 0,
                "is_admin_path": 1 if re.search(r"/admin|/config|/\.git", line) else 0,
                "is_web": 1 if "GET" in line or "POST" in line else 0,
                "is_cron": 1 if "CRON" in line else 0,
            }
            records.append(record)

    return pd.DataFrame(records)
