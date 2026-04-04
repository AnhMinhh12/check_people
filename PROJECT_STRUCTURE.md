# 📁 Cấu Trúc Dự Án — HTMP_AI_Systems Layout

> **Áp dụng cho**: Sentinel Warden AI V5.5 Enterprise  
> **Kiến trúc**: Modular, phân tách rõ ràng trách nhiệm

---

## Sơ Đồ Tổng Quan

```text
check_person/                         (HTMP_AI_Systems Layout)
│
├── app/                              # 🚀 Điểm khởi chạy (Entry Point)
│   ├── __init__.py
│   ├── main.py                       # Flask + SocketIO + Camera Sync + Worker Start
│   └── routes.py                     # REST API endpoints (/api/history, /api/health, ...)
│
├── core/                             # ⚙️ Cấu hình lõi (Environment, Constants, Logging)
│   ├── __init__.py
│   ├── config.py                     # Class Settings — tập trung toàn bộ biến .env
│   ├── constants.py                  # Hằng số hệ thống (trạng thái, ngưỡng, tên bảng DB)
│   └── logging.py                    # Cấu hình logging tập trung (console + file per camera)
│
├── db/                               # 💾 Tương tác cơ sở dữ liệu (SQLAlchemy + Repository Pattern)
│   ├── __init__.py
│   ├── connection.py                 # Engine, Session, pooling (SQLite dev / MySQL production)
│   ├── models.py                     # ORM models: Camera, Violation (SQLAlchemy)
│   └── repository.py                 # CameraRepository, ViolationRepository (Repository Pattern)
│
├── events/                           # 📡 Quản lý sự kiện (Pub/Sub Pattern)
│   ├── __init__.py
│   └── dispatcher.py                 # EventDispatcher — phát/nhận sự kiện decoupled
│
├── integrations/                     # 🔗 Tích hợp hệ thống bên ngoài
│   ├── __init__.py
│   ├── telegram.py                   # TelegramNotifier — cảnh báo qua Telegram Bot
│   └── erp.py                        # ERPConnector — đồng bộ dữ liệu vi phạm lên ERP/MES
│
├── pipelines/                        # 🔄 Luồng xử lý AI (Video → Inference → Kết quả)
│   ├── __init__.py
│   ├── camera_stream.py              # CameraStreamer — thread đọc RTSP liên tục
│   ├── worker_manager.py             # WorkerManager — quản lý lifecycle AI Workers
│   └── ai_worker.py                  # AIWorker — thread xử lý AI + violation logic per camera
│
├── services/                         # 🧠 Nghiệp vụ AI cụ thể
│   ├── __init__.py
│   └── ai_engine.py                  # AIEngine — YOLO inference, ROI overlap, persistence buffer
│
├── templates/                        # 🖥️ Giao diện Web Dashboard (Jinja2)
│   ├── layouts/base.html
│   ├── partials/header.html, sidebar.html, modals.html
│   ├── components/dashboard_grid.html, focused_view.html, ...
│   └── index.html
│
├── data/                             # 📊 Dữ liệu file runtime (Git ignored)
│   ├── sentinel.db                   # SQLite database (chỉ dùng trong Dev)
│   ├── roi_config_*.json             # Cấu hình ROI per camera
│   └── violations/                   # Ảnh bằng chứng vi phạm
│
├── models/                           # 🤖 Mô hình AI (Git ignored)
│   └── yolov8s.onnx                  # ONNX Runtime optimized (45MB)
│
├── logs/                             # 📋 Nhật ký hoạt động (Git ignored)
│   └── camera_{id}.log
│
├── scripts/                          # 🛠️ Công cụ tiện ích
│   ├── migrate_db.py
│   ├── seed_test_data.py
│   └── wifi.py
│
├── docs/                             # 📚 Tài liệu hệ thống
│
├── .env.example                      # Mẫu biến môi trường
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Ý Nghĩa Từng Module

| Module | Trách nhiệm | Phụ thuộc vào |
|---|---|---|
| `app/` | Khởi chạy server, routing API | `core`, `db`, `pipelines` |
| `core/` | Cấu hình, hằng số, logging | Không phụ thuộc module nào |
| `db/` | SQLAlchemy ORM + Repository Pattern (SQLite/MySQL) | `core` |
| `events/` | Pub/Sub sự kiện decoupled | `core` |
| `integrations/` | Kết nối bên ngoài (Telegram, ERP) | `core` |
| `pipelines/` | Luồng video → AI → kết quả | `core`, `db`, `services` |
| `services/` | Logic AI (inference, tracking, NMS) | `core` |

---

## Cách Chạy

```bash
# Chạy trực tiếp
python -m app.main

# Chạy bằng Docker
docker-compose up --build
```
