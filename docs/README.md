# Sentinel Warden - Hệ Thống Giám Sát An Toàn Công Nghiệp AI

[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-green.svg)](https://flask.palletsprojects.com/)
[![AI Engine](https://img.shields.io/badge/AI-YOLOv8-red.svg)](https://github.com/ultralytics/ultralytics)

Hệ thống giám sát thời gian thực dựa trên trí tuệ nhân tạo (AI) để phát hiện sự hiện diện của nhân viên trong vùng an toàn (ROI). Tự động ghi lại bằng chứng vi phạm và cảnh báo tức thì qua giao diện Web.

## 🚀 Tính Năng Chính
- **Giám sát thời gian thực**: Kết nối luồng RTSP từ camera IP công nghiệp.
- **Phát hiện người (AI)**: Sử dụng YOLOv8-Nano tối ưu hóa cho tốc độ xử lý cao.
- **ROI Đa Giác (Polygonal ROI)**: Cấu hình vùng an toàn linh hoạt ngay trên giao diện web.
- **Ghi nhật ký vi phạm**: Tự động lưu ảnh bằng chứng và thời lượng vi phạm vào SQLite database.
- **Giao diện Dashboard cao cấp**: Hiển thị FPS, trạng thái kết nối và lịch sử vi phạm thời gian thực.

## 🛠 Yêu Cầu Hệ Thống
- **OS**: Windows / Linux / macOS
- **Python**: 3.8 trở lên
- **Hardware**: CPU Core i5+ hoặc GPU NVIDIA (khuyên dùng để tăng FPS)

## 📦 Hướng Dẫn Cài Đặt

1. **Clone project và truy cập thư mục**:
   ```bash
   cd check_person
   ```

2. **Tạo và kích hoạt môi trường ảo**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Cài đặt thư viện**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Cấu hình file `.env`**:
   Sửa file `.env` ở thư mục gốc:
   ```env
   RTSP_URL=rtsp://your_camera_url
   MODEL_PATH=yolov8n.pt
   FLASK_PORT=5000
   ALARM_DELAY_SECONDS=5.0
   ```

## 🖥 Chạy Ứng Dụng
```powershell
python app.py
```
Sau đó truy cập: `http://localhost:5000`

## 📂 Cấu Trúc Thư Mục (Modular Architecture)
- `src/core/`: Logic xử lý AI và Camera Stream.
- `src/database/`: Quản lý lưu trữ dữ liệu vi phạm.
- `src/services/`: Worker chạy nền xử lý luồng AI.
- `src/api/`: Các endpoint API và SocketIO.
- `templates/`: Giao diện người dùng (Frontend).

## 🐳 Triển Khai Với Docker (Khuyên Dùng)

Nếu bạn đã cài đặt Docker Desktop, bạn có thể chạy dự án mà không cần cài đặt Python cục bộ:

1. **Khởi chạy container**:
   ```bash
   docker-compose up --build -d
   ```

2. **Dừng hệ thống**:
   ```bash
   docker-compose down
   ```

Lưu ý: Các dữ liệu như `sentinel.db`, `roi_config.json`, và ảnh trong thư mục `violations/` sẽ được đồng bộ trực tiếp với máy host, nên bạn sẽ không bị mất dữ liệu khi xóa container.

## 📄 Giấy Phép
Dự án được phát triển nội bộ cho mục đích giám sát an toàn lao động.
