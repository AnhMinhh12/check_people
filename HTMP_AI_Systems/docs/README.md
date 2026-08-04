# 🛡️ Sentinel Warden AI — Safety Monitoring Platform

[![CI/CD](https://github.com/Dunghq23/HTMP_AI_Systems/actions/workflows/docker-build.yml/badge.svg?branch=dev/AnhMinh)](https://github.com/Dunghq23/HTMP_AI_Systems/actions?query=branch%3Adev%2FAnhMinh)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![YOLO](https://img.shields.io/badge/YOLOv8s-ONNX-00FFFF?logo=yolo)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)

**Nền tảng giám sát an toàn lao động bằng AI** đa luồng (Multi-Camera), tối ưu hóa ONNX Runtime cho hiệu năng cực cao và kiến trúc Zero-Spin.

> **Phiên bản hiện tại**: V5.6 Enterprise Edition (Zero-Spin ONNX)
> **Phần cứng đã test**: Intel Core i7-1355U (Gen 13)
> **Camera đã test**: Hikvision RTSP

---

## ✨ Tính năng Chính

| Tính năng | Mô tả |
|---|---|
| 🧠 **AI Nhận diện (YOLOv8s)** | Shared Model AI nạp 1 lần, 0% CPU rác (Zero-Spin ONNX architecture) |
| 🛡 **Tối ưu H264 & Luồng** | Ép chặn FFMPEG Spin-Wait, gánh mượt 10-15 Camera trên Server nhỏ |
| 🛡 **Quản lý Đa Camera** | Hỗ trợ nhiều luồng RTSP đồng thời, cấu hình qua file `.env` |
| 🧹 **Dọn dẹp DB Tự động** | Hard Delete — Tự động xóa camera không còn trong `.env` |
| ⏱️ **Cảnh báo Thông minh** | Bộ đệm 1 giây chống nháy + ngưỡng 5 giây xác nhận vi phạm |
| 📸 **Ghi bằng chứng** | Tự động chụp ảnh kèm Bounding Box khi vi phạm |
| 🖥️ **Dashboard Premium** | Typography Inter chuẩn Enterprise, HUD cảnh báo, UI tiếng Việt |
| ⚙️ **Vẽ ROI trực tiếp** | Chuột trái chấm điểm, chuột phải hoàn tác, hot-reload không cần restart |
| 🐋 **Docker & CI/CD** | Push code → Tự động Build + Push Image lên GitHub Registry |

---

## 🚀 Cài đặt & Chạy

### Yêu cầu
- Python 3.11 (Bản chuyên biệt yêu cầu khắt khe để đảm bảo hiệu suất AI và tránh lỗi ghi đè hệ điều hành)
- Camera IP hỗ trợ RTSP
- Kết nối mạng LAN (khuyến nghị cáp Ethernet)

### Cài đặt Local

```bash
# 1. Clone repository
git clone -b dev/AnhMinh https://github.com/Dunghq23/HTMP_AI_Systems.git
cd HTMP_AI_Systems

# 2. Tạo môi trường ảo
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Cài đặt thư viện
pip install -r requirements.txt

# 4. Cấu hình Camera (chỉnh file .env)
copy .env.example .env  # (Hoặc dùng `cp .env.example .env` trên hệ điều hành Linux)

# 5. Chạy hệ thống
# Đối với môi trường phát triển (Windows Local):
python -m app.main

# Đối với môi trường Server thật sự (Linux) đã có GPU:
# Hãy chạy file shell kịch bản gốc để tối ưu tải GPU và fix lỗi môi trường Cuda
bash run.sh
```

Mở trình duyệt: **http://localhost:5000**

### Triển khai Docker

```bash
docker-compose up -d
```

---

## ⚙️ Cấu hình

### File `.env`
```env
# Cụm Camera (hỗ trợ đến RTSP_URL100)
RTSP_URL1=rtsp://admin:password@192.168.1.10:554/stream
CAMERA_NAME1=Máy Hàn 01

RTSP_URL2=rtsp://admin:password@192.168.1.11:554/stream
CAMERA_NAME2=Kho Bãi

# AI Settings
MODEL_PATH=models/yolov8s.onnx
CONFIDENCE_THRESHOLD=0.15
ALARM_DELAY_SECONDS=5.0
AI_MAX_FPS=10

FLASK_DEBUG=False
```

### Các thông số nâng cao

| Thông số | Giá trị | File | Tác dụng |
|---|---|---|---|
| `max_memory_frames` | `5` | `services/ai_engine.py` | Số frame giữ vết người (chống nháy) |
| Bộ đệm trạng thái | `1.0s` | `pipelines/ai_worker.py` | Chờ 1s xác nhận trước khi đổi trạng thái |
| Dashboard emit | `0.25s` | `pipelines/ai_worker.py` | Tần suất gửi data real-time (4Hz) |
| JPEG Quality | `40` | `pipelines/ai_worker.py` | Chất lượng ảnh truyền lên Dashboard |

---

## 📁 Cấu trúc Dự án

```text
HTMP_AI_Systems/
│
├── app/                          # 🚀 Entry Point
│   ├── main.py                   # Flask + SocketIO + Camera Sync + Worker Start
│   └── routes.py                 # REST API endpoints
│
├── core/                         # ⚙️ Cấu hình lõi
│   ├── config.py                 # Class Settings — load toàn bộ biến .env
│   ├── constants.py              # Hằng số hệ thống
│   └── logging.py                # Logging tập trung (console + file per camera)
│
├── db/                           # 💾 Database (SQLAlchemy + Repository Pattern)
│   ├── connection.py             # Engine, Session, pooling
│   ├── models.py                 # ORM: Camera, Violation
│   └── repository.py             # CameraRepository, ViolationRepository
│
├── events/                       # 📡 Pub/Sub sự kiện
│   └── dispatcher.py             # EventDispatcher — decoupled event bus
│
├── integrations/                 # 🔗 Tích hợp bên ngoài
│   ├── telegram.py               # TelegramNotifier
│   └── erp.py                    # ERPConnector
│
├── pipelines/                    # 🔄 Luồng xử lý AI
│   ├── camera_stream.py          # CameraStreamer — thread đọc RTSP
│   ├── worker_manager.py         # WorkerManager — lifecycle AI Workers
│   └── ai_worker.py              # AIWorker — logic vi phạm per camera
│
├── services/                     # 🧠 AI Engine
│   └── ai_engine.py              # YOLOv8s inference, ROI, persistence buffer
│
├── templates/                    # 🖥️ Web Dashboard (Jinja2 + HTML/JS)
│   └── index.html
│
├── data/                         # 📊 Dữ liệu runtime (git ignored)
│   ├── sentinel.db               # SQLite database
│   ├── roi_config_*.json         # Cấu hình ROI per camera
│   └── violations/               # Ảnh bằng chứng vi phạm
│
├── models/                       # 🤖 Model AI (git ignored)
│   └── yolov8s.onnx              # ONNX Runtime optimized (~45MB)
│
├── logs/                         # 📋 Nhật ký per camera (git ignored)
├── scripts/                      # 🛠️ Công cụ tiện ích
├── docs/                         # 📚 Tài liệu
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### Phụ thuộc giữa các module

| Module | Trách nhiệm | Phụ thuộc vào |
|---|---|---|
| `app/` | Khởi chạy server, routing API | `core`, `db`, `pipelines` |
| `core/` | Cấu hình, hằng số, logging | Không phụ thuộc ai |
| `db/` | ORM + Repository Pattern | `core` |
| `events/` | Pub/Sub sự kiện decoupled | `core` |
| `integrations/` | Kết nối Telegram, ERP | `core` |
| `pipelines/` | Video → AI → Kết quả | `core`, `db`, `services` |
| `services/` | Logic AI (inference, NMS, ROI) | `core` |

---

## 🛠️ Hướng dẫn Vẽ Vùng An Toàn (ROI)

1. Truy cập tab **Cấu Hình** trên Dashboard
2. **Chuột Trái**: Click để chấm điểm — tạo hình đa giác bao quanh vị trí làm việc
3. **Chuột Phải**: Click để xóa điểm vừa vẽ sai (hoàn tác)
4. Nhấn **"Lưu Cấu Hình"** → AI hot-reload ngay lập tức (không cần restart)

> **💡 Mẹo**: Vẽ vùng rộng hơn thực tế một chút — AI dùng Mask Overlap nên chỉ cần bất kỳ điểm nào của người lọt vào ROI là được tính An Toàn.

---

## 📊 Giao diện Dashboard

| Tab | Chức năng |
|---|---|
| **Giám Sát** | Camera live + Bounding Box + ROI + FPS + Trạng thái |
| **Nhật Ký** | Bảng lịch sử vi phạm kèm ảnh bằng chứng |
| **Phân Tích** | Thống kê tỉ lệ trực vị trí, tổng giờ rời máy |
| **Cấu Hình** | Vẽ vùng an toàn ROI trực tiếp trên camera live |

### Trạng thái AI

| Trạng thái | Điều kiện | Hiển thị |
|---|---|---|
| ✅ **AN TOÀN** | Có người trong ROI, hoặc vắng < 1s | Chữ xanh cyan |
| ⚠️ **RỜI VỊ TRÍ** | Vắng 1s – 5s | Thanh bar đỏ chạy |
| 🚨 **VI PHẠM** | Vắng ≥ 5s | HUD đỏ toàn màn hình |

---

## 🔗 API Endpoints

| Method | URL | Mô tả |
|---|---|---|
| GET | `/` | Dashboard chính |
| GET | `/api/cameras` | Danh sách camera |
| GET | `/api/history` | 50 vi phạm gần nhất (filter by `?camera_id=`) |
| GET | `/api/analytics` | Thống kê vi phạm (filter by `?camera_id=`) |
| GET | `/api/health` | Health check |
| POST | `/api/config_roi` | Lưu ROI mới (`{camera_id, points}`) |
| GET | `/violations/<file>` | Ảnh bằng chứng |
| WS | `stats_update_{id}` | Real-time data stream per camera |

---

## 📖 Tài liệu Chi tiết

| File | Nội dung |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Kiến trúc kỹ thuật: luồng dữ liệu, threading, database, Docker |
| [ROADMAP.md](ROADMAP.md) | Lộ trình mở rộng: 5→20→100 camera, GPU server, chi phí |
| [GPU_MIGRATION.md](GPU_MIGRATION.md) | Hướng dẫn nâng cấp và chuyển đổi sang nền tảng máy chủ NVIDIA GPU |
| [SERVER_SETUP_LOG.md](SERVER_SETUP_LOG.md) | Sổ tay ghi chép chi tiết các quá trình tinh chỉnh cài đặt trên Server (Python 3.11, run.sh, Netdata...) |

---

© 2026 Sentinel Warden AI — Industrial Safety Monitoring Platform
