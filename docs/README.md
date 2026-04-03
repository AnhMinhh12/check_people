    # 🛡️ Sentinel Warden AI — Safety Monitoring Platform

[![CI/CD](https://github.com/AnhMinhh12/check_people/actions/workflows/docker-build.yml/badge.svg)](https://github.com/AnhMinhh12/check_people/actions)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![YOLO](https://img.shields.io/badge/YOLOv8s-Small-00FFFF?logo=yolo)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Internal-gray)

**Nền tảng giám sát an toàn lao động bằng AI** cho môi trường sản xuất công nghiệp. Tự động nhận diện người qua camera RTSP, cảnh báo khi công nhân rời vị trí, ghi ảnh bằng chứng vi phạm.

> **Phiên bản hiện tại**: V4.5 Industrial Edition  
> **Phần cứng đã test**: Intel Core i7-1355U (Gen 13)  
> **Camera đã test**: Hikvision RTSP  

---

## ✨ Tính năng Chính

| Tính năng | Mô tả |
|---|---|
| 🧠 **AI Nhận diện (YOLOv8s)** | Phát hiện người với độ chính xác cao, kể cả khi cúi/quay lưng |
| 🔒 **Bám dính Đối tượng** | Bộ nhớ đệm 5 frame — Bounding Box không bao giờ bị "nháy" |
| 📐 **Quét 5 điểm Dọc thân** | Từ chân lên vai, chỉ cần 1/5 điểm trong ROI = AN TOÀN |
| ⏱️ **Cảnh báo thông minh** | Đệm 1s chống nháy → Cảnh báo RỜI VỊ TRÍ → VI PHẠM sau 5s |
| 📸 **Ghi bằng chứng** | Tự động chụp ảnh có Bounding Box + ROI, lưu vào Database |
| 🖥️ **Dashboard Premium** | Giao diện Glassmorphism, 4 tab, HUD cảnh báo toàn màn hình |
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

### File `.env`
```env
# Camera
RTSP_URL=rtsp://admin:password@192.168.1.10:554/Streaming/Channels/102

# Server
FLASK_PORT=5000
FLASK_DEBUG=False

# AI
MODEL_PATH=yolov8s.pt          # yolov8n.pt (nhanh) | yolov8s.pt (chính xác)
CONFIDENCE_THRESHOLD=0.15       # Ngưỡng tin cậy (0.15 = nhạy, 0.5 = chắc chắn)
ALARM_DELAY_SECONDS=5.0         # Giây vắng mặt trước khi ghi vi phạm
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
check_person/
├── app.py                      # Entry point chính
├── .env                        # Cấu hình môi trường
├── roi_config.json             # Tọa độ vùng an toàn
├── requirements.txt            # Dependencies
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Docker orchestration
├── src/
│   ├── core/
│   │   ├── ai_engine.py        # AI: YOLOv8s + Tracking + Persistence + NMS
│   │   ├── camera_stream.py    # Đọc RTSP trong thread riêng
│   │   └── database.py         # SQLite manager
│   ├── services/
│   │   └── ai_worker.py        # Logic vi phạm + ghi bằng chứng
│   ├── api/
│   │   └── routes.py           # REST API endpoints
│   └── tests/
│       └── test_basic.py       # Unit tests
├── templates/
│   └── index.html              # Web Dashboard (4 tabs)
├── violations/                 # Ảnh bằng chứng vi phạm
├── docs/                       # Tài liệu
│   ├── mo_ta.md                # Mô tả chi tiết hệ thống
│   ├── ARCHITECTURE.md         # Kiến trúc kỹ thuật
│   ├── README.md               # File này
│   └── ROADMAP.md              # Lộ trình phát triển & mở rộng
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
