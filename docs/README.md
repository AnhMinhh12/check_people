    # 🛡️ Sentinel Warden AI — Safety Monitoring Platform

[![CI/CD](https://github.com/AnhMinhh12/check_people/actions/workflows/docker-build.yml/badge.svg)](https://github.com/AnhMinhh12/check_people/actions)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![YOLO](https://img.shields.io/badge/YOLOv8s-Small-00FFFF?logo=yolo)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Internal-gray)

**Nền tảng giám sát an toàn lao động bằng AI** đa luồng (Multi-Camera), quản lý tập trung và dọn dẹp Database tự động.
 
> **Phiên bản hiện tại**: V5.0 Enterprise Edition
> **Phần cứng đã test**: Intel Core i7-1355U (Gen 13)  
> **Camera đã test**: Hikvision RTSP  

---

## ✨ Tính năng Chính

| Tính năng | Mô tả |
|---|---|
| 🧠 **AI Nhận diện (YOLOv8n)** | Phát hiện người đa luồng, tối ưu hóa cho CPU với bộ nhớ đệm chống nháy |
| 🛡 **Quản lý Đa Camera** | Hỗ trợ 100+ luồng RTSP đồng thời, cấu hình linh hoạt qua file `.env` |
| 🧹 **Dọn dẹp DB Tự động** | Cơ chế **Hard Delete** — Tự động xóa camera rác không có trong file cấu hình |
| ⏱️ **Cảnh báo Thông minh** | Hiển thị vạch ngưỡng vắng mặt trực quan trên thanh tiến trình Dashboard |
| 📸 **Ghi bằng chứng** | Tự động chụp ảnh kèm Bounding Box, ghi tên Camera vào lịch sử vi phạm |
| 🖥️ **Dashboard Premium** | Giao diện Glassmorphism V5.0, HUD cảnh báo toàn màn hình, cột Tên Camera trong Nhật ký |
| ⚙️ **Vẽ ROI trực tiếp** | Chuột trái chấm điểm, chuột phải hoàn tác, có hướng dẫn |
| 🐋 **Docker & CI/CD** | Push code → Tự động Build + Push Image lên GitHub Registry |

---

## 🚀 Cài đặt & Chạy

### Yêu cầu
- Python 3.10+ (khuyến nghị 3.11)
- Camera IP hỗ trợ RTSP
- Kết nối mạng LAN (khuyến nghị cáp Ethernet)

### Cài đặt Local

```bash
# 1. Clone repository
git clone https://github.com/AnhMinhh12/check_people.git
cd check_people

# 2. Tạo môi trường ảo
python -m venv venv

# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. Cài đặt thư viện
pip install -r requirements.txt

# 4. Cấu hình Camera
# Chỉnh sửa RTSP_URL trong file .env hoặc app.py

# 5. Chạy hệ thống
python app.py
```

Mở trình duyệt: **http://localhost:5000**

### Triển khai Docker

```bash
# Cách 1: Dùng Docker Compose (Khuyến nghị)
docker-compose up -d

# Cách 2: Dùng Image trên GitHub Registry
docker pull ghcr.io/anhminhh12/check_people:main
docker run -d --name warden -p 5000:5000 ghcr.io/anhminhh12/check_people:main
```

---

## ⚙️ Cấu hình

### File `.env` (Cấu hình đa Camera)
```env
# Camera 1
RTSP_URL1=rtsp://admin:password@ip_address_1:554/stream
CAMERA_NAME1=Máy Hàn 01

# Camera 2
RTSP_URL2=rtsp://admin:password@ip_address_2:554/stream
CAMERA_NAME2=Kho Bãi

# ... hỗ trợ tới RTSP_URL100

# AI Settings
MODEL_PATH=models/yolov8n.pt     # Nâng cấp lên Nano cho hệ thống đa luồng
CONFIDENCE_THRESHOLD=0.15
ALARM_DELAY_SECONDS=5.0
```

### Các thông số nâng cao (trong code)

| Thông số | Giá trị | File | Tác dụng |
|---|---|---|---|
| `max_memory_frames` | `5` | `ai_engine.py` | Số frame giữ vết người (chống nháy) |
| Bộ đệm trạng thái | `1.0s` | `ai_worker.py` | Chờ 1s xác nhận trước khi chuyển trạng thái |
| Dashboard emit | `0.2s` | `ai_worker.py` | Tần suất gửi data real-time (5Hz) |
| JPEG Quality | `50` | `ai_worker.py` | Chất lượng ảnh truyền lên Dashboard |

---

## 🛠️ Hướng dẫn Vẽ Vùng An Toàn (ROI)

1. Truy cập tab **Cấu Hình** trên Dashboard
2. **Chuột Trái**: Click để chấm điểm — Tạo hình đa giác bao quanh vị trí làm việc
3. **Chuột Phải**: Click để xóa điểm vừa vẽ sai (hoàn tác)
4. Nhấn **"Lưu Cấu Hình"** để AI bắt đầu áp dụng vùng mới
5. AI sẽ **tự động tải lại ROI** ngay lập tức (hot reload, không cần restart)

> **💡 Mẹo**: Nên vẽ vùng rộng hơn thực tế một chút — AI V4.5 quét đến tận vai nên cần đủ không gian phía trên đầu công nhân.

---

## 📊 Giao diện Dashboard

### 4 Tab chính

| Tab | Chức năng |
|---|---|
| **Giám Sát** | Camera live + Bounding Box + ROI + FPS + Trạng thái + Thanh thời gian + Nhật ký |
| **Nhật Ký** | Bảng lịch sử vi phạm kèm ảnh bằng chứng, click để phóng to |
| **Phân Tích** | Thống kê tỉ lệ trực vị trí, tổng giờ rời máy, biểu đồ xu hướng tuần |
| **Cấu Hình** | Vẽ vùng an toàn ROI trực tiếp trên camera live + Panel hướng dẫn |

### Trạng thái hệ thống

| Trạng thái | Hiển thị | Điều kiện |
|---|---|---|
| ✅ AN TOÀN | Chữ xanh cyan | Có người trong ROI |
| ⚠️ RỜI VỊ TRÍ | Thanh bar đỏ chạy | Vắng mặt 1s–5s |
| 🚨 VI PHẠM | HUD đỏ toàn màn hình | Vắng mặt ≥ 5s |

---

## 📁 Cấu trúc Dự án

```
├── data/                       # Dữ liệu động (DB, ROI, Violations)
├── models/                     # Mô hình AI (.pt)
├── logs/                       # Nhật ký hoạt động
├── scripts/                    # Các công cụ hỗ trợ
├── src/
│   ├── core/
│   │   ├── ai_engine.py        # AI: YOLOv8s + Tracking + Persistence + NMS
│   │   ├── camera_stream.py    # Đọc RTSP trong thread riêng
│   │   └── database.py         # Database Manager V5.0
│   ├── services/
│   │   └── ai_worker.py        # Logic vi phạm + ghi bằng chứng
│   ├── api/
│   │   └── routes.py           # REST API endpoints
├── templates/
│   └── index.html              # Web Dashboard (4 tabs)
├── docs/                       # Tài liệu
└── .github/workflows/
    └── docker-build.yml        # CI/CD tự động
```

---

## 📖 Tài liệu Chi tiết

| File | Nội dung |
|---|---|
| [mo_ta.md](mo_ta.md) | Mô tả đầy đủ hệ thống: Logic, thông số, API, cấu hình |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Kiến trúc kỹ thuật: Sơ đồ luồng, threading, database, Docker |
| [ROADMAP.md](ROADMAP.md) | Lộ trình mở rộng: 5→20→100 camera, GPU server, chi phí |

---

## 🔗 API Endpoints

| Method | URL | Mô tả |
|---|---|---|
| GET | `/` | Dashboard chính |
| GET | `/api/history` | 50 vi phạm gần nhất |
| GET | `/api/health` | Health check |
| POST | `/api/config_roi` | Lưu ROI mới |
| GET | `/violations/<file>` | Ảnh bằng chứng |
| WS | `stats_update` | Real-time data stream |

---

© 2026 Sentinel Warden AI — Industrial Safety Monitoring Platform
