import joblib
import pandas as pd
import matplotlib.pyplot as plt
from log_parser import parse_log_file
from sklearn.metrics import precision_recall_curve, classification_report

# Load model và đặc trưng
model = joblib.load("model/model.pkl")
feature_columns = joblib.load("model/feature_columns.pkl")

# Đọc dữ liệu
df = parse_log_file("data/Sys.log")
X = df[feature_columns]

# Dự đoán
df["score"] = model.decision_function(X)

# Gán nhãn thật (giả lập)
df["true_label"] = 1  # bình thường
df.loc[
    (df["is_failed_login"] == 1) |
    (df["is_admin_path"] == 1) |
    (df["is_root_access"] == 1),
    "true_label"
] = -1  # bất thường

# Chuyển nhãn về dạng nhị phân: 1 = anomaly, 0 = normal
y_true = (df["true_label"] == -1).astype(int)
y_scores = -df["score"]  # đảo dấu vì score càng âm → càng bất thường

# Tính Precision–Recall curve
precision, recall, thresholds = precision_recall_curve(y_true, y_scores)

# Vẽ biểu đồ
plt.figure()
plt.plot(recall, precision, marker='.')
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Precision–Recall Curve for Isolation Forest")
plt.grid(True)
plt.show()

# In báo cáo với threshold mặc định (0)
df["prediction"] = df["score"].apply(lambda x: -1 if x < 0 else 1)
print("Classification Report (default threshold = 0):")
print(classification_report(df["true_label"], df["prediction"]))
