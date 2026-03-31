# Sử dụng image Python 3.11 dạng slim để tương thích thư viện mới
FROM python:3.11-slim

# Ngăn Python tạo file .pyc và bật log trực tiếp ra console
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết cho OpenCV và YOLO
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Nâng cấp pip và cài đặt Torch bản rút gọn (CPU Only) để tải nhanh và nhẹ dĩa D
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Mở port 5000 cho Flask
EXPOSE 5000

# Lệnh khởi chạy ứng dụng
CMD ["python", "app.py"]
