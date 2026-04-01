# Sentinel Warden - Hệ Thống Giám Sát An Toàn Công Nghiệp AI (V4.0)

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-green.svg)](https://flask.palletsprojects.com/)
[![AI Engine](https://img.shields.io/badge/AI-YOLOv8-red.svg)](https://github.com/ultralytics/ultralytics)

Hệ thống giám sát thời gian thực dựa trên trí tuệ nhân tạo (AI) để phát hiện sự hiện diện của nhân sự trong vùng an toàn (ROI). Tự động ghi lại bằng chứng vi phạm và cảnh báo tức thì qua giao diện Web Dashboard.

---

## 🚀 Tính Năng Nổi Bật (V4.0)

- **Multi-point Vertical Scanning**: Thuật toán quét 4 điểm dọc (100%, 90%, 75%, 50% chiều cao) giúp nhận diện ổn định ngay cả khi bị che khuất một phần.
- **Confirmation Logic (1s)**: Cơ chế đệm 1 giây giúp loại bỏ hiện tượng "nháy" trạng thái do AI mất dấu khung hình ngắn hạn.
- **Real-time Web Dashboard**: Cập nhật trạng thái và hình ảnh 5Hz qua SocketIO, mang lại trải nghiệm mượt mà, không giật lag.
- **Dynamic ROI configuration**: Cho phép thay đổi vùng giám sát trực tiếp từ trình duyệt và áp dụng tức thì xuống Backend.
- **Advanced Evidence Collection**: Tự động chụp ảnh vi phạm kèm khung nhận diện (Annotated Images) và lưu vào SQLite database.
- **Automatic NMS Optimization**: Tự động lọc bỏ các bounding box bị chia cắt do vật cản phần cứng tại hiện trường.

---

## 🛠 Yêu Cầu Hệ Thống

- **Hệ điều hành**: Windows 10/11, Linux (Ubuntu 20.04+)
- **Python**: 3.9 trở lên
- **Phần cứng**: CPU Intel Core i5 Gen 10th+ hoặc GPU NVIDIA (Khuyên dùng để đạt 15+ FPS)
- **Camera**: Luồng RTSP chuẩn (H.264/H.265)

---

## 📦 Hướng Dẫn Cài Đặt

1. **Chuẩn bị môi trường**:
   ```bash
   cd check_person
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Cài đặt thư viện**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình**:
   Hệ thống đọc cấu hình camera trực tiếp trong `app.py` hoặc qua biến môi trường. Mặc định chạy tại cổng `5000`.

---

## 🖥 Khởi Chạy

```powershell
python app.py
```
Sau đó truy cập: `http://localhost:5000`

---

## 📂 Kiến Trúc Dự Án (Modular Architecture)

- `src/core/`: Logic lõi hệ thống (AI Engine, Camera Stream, Database).
- `src/services/`: Các background worker xử lý luồng AI liên tục.
- `src/database/`: Các logic phụ trợ về lưu trữ và truy xuất lịch sử.
- `src/api/`: Các endpoint Flask và SocketIO Events.
- `templates/`: Giao diện Dashboard (HTML/CSS/JS).

---

## 🐳 Triển Khai Với Docker

Triển khai nhanh chóng với Docker Compose:
```bash
docker-compose up --build -d
```
Dữ liệu vi phạm và cấu hình được mount trực tiếp vào host qua Volumes để đảm bảo tính bền vững.

---

## 📄 Tài Liệu Chi Tiết
- [Mô tả chi tiết tính năng](docs/mo_ta.md)
- [Kiến trúc hệ thống chi tiết](docs/ARCHITECTURE.md)
