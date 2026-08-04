#!/bin/bash

# 1. Tự động nạp đường dẫn thư viện NVIDIA
export LD_LIBRARY_PATH=$(find $HOME/.local/lib/python3.11/site-packages/nvidia -type d -name "lib" | tr '\n' ':')$LD_LIBRARY_PATH

# 2. Chặn tự động cập nhật để bảo vệ GPU
export YOLO_OFFLINE=True
export ULTRALYTICS_OFFLINE=True

# 3. Chạy ứng dụng
echo ">>> ĐANG KHỞI ĐỘNG HỆ THỐNG WARDEN AI TOÀN DIỆN..."
python3.11 -m app.main
