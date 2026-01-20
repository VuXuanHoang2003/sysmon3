# Sysmon3 - Hệ thống giám sát và phát hiện bất thường

## Mô tả

Hệ thống giám sát và phát hiện các hoạt động bất thường trong log sử dụng Machine Learning.

## Cài đặt

### Yêu cầu hệ thống

- Python 3.14

### Cài đặt các thư viện

```bash
pip install -r requirements.txt
```

## Hướng dẫn sử dụng

### 1. Huấn luyện mô hình

```bash
python train_model.py
```

### 2. Đánh giá mô hình

```bash
python evaluate_model.py
```

### 3. Sinh log thử nghiệm

```bash
python generate_test_logs.py
```

### 4. Phát hiện & cảnh báo

```bash
python detect_log.py
```

## Cấu trúc thư mục

```text
sysmon3/
├── data/           # Dữ liệu huấn luyện và test
├── logs/           # File log
├── model/          # Mô hình đã huấn luyện
├── __pycache__/    # Python cache
├── alerting.py     # Module cảnh báo
├── detect_log.py   # Phát hiện bất thường
├── evaluate_model.py   # Đánh giá mô hình
├── generate_test_logs.py   # Sinh log test
├── log_parser.py   # Phân tích log
├── telegram_alert.py   # Cảnh báo qua Telegram
├── train_model.py  # Huấn luyện mô hình
├── requirements.txt    # Danh sách thư viện
└── readme.md       # Tài liệu hướng dẫn
```
