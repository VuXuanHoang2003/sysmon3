import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from log_parser import parse_log_file
import os

# Tạo thư mục model nếu chưa có
os.makedirs("model", exist_ok=True)

# Đọc dữ liệu
df = parse_log_file("data/Sys.log")

# Lưu danh sách cột đặc trưng
feature_columns = df.columns.tolist()

# Chia train/test
X_train, X_test = train_test_split(df, test_size=0.2, random_state=42)

# Khởi tạo mô hình Isolation Forest
model = IsolationForest(
    n_estimators=200,
    contamination=0.05,   # giả định 5% log là bất thường
    random_state=42
)

# Huấn luyện
model.fit(X_train)

# Lưu mô hình và cấu trúc đặc trưng
joblib.dump(model, "model/model.pkl")
joblib.dump(feature_columns, "model/feature_columns.pkl")

print("✅ Huấn luyện xong và đã lưu mô hình vào thư mục model/")
