# Image Python 3.11 Slim - Hiệu năng cao & Tối ưu Đa Camera (V5.0 Enterprise)
FROM python:3.11-slim

# Ngăn Python tạo file .pyc và bật log trực tiếp ra console
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (OpenCV, YOLO, HealthCheck)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Pip & Dependencies (Cơ chế Catching giúp build nhanh hơn)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    # Cài đặt Torch bản rút gọn (CPU Only) để bản build nhẹ dĩa cứng
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Mở port 5000 cho Server
EXPOSE 5000

# Metadata nhãn của dự án (Tùy chọn)
LABEL maintainer="it07"
LABEL version="5.0"
LABEL description="Sentinel Warden AI Safety Monitoring System - Enterprise Edition"

# Lệnh khởi chạy chính
# Sử dụng trực tiếp app.py với Flask-SocketIO + eventlet (từ requirements)
CMD ["python", "app.py"]
