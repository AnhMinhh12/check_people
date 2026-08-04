# PERSON_HTMP

Hệ thống giám sát an toàn lao động tích hợp AI cho môi trường công nghiệp — phát hiện vi phạm khu vực (ROI), cảnh báo thời gian thực và đồng bộ với ERP.

> **Refactor 2026** — chuyển sang cấu trúc module, thống nhất `HTMP_AI_Systems/` làm package chính.

---

## ✨ Tính năng

- 🎥 **Đa luồng camera** — xử lý song song nhiều nguồn RTSP/USB
- 🤖 **AI nhận diện vi phạm** — YOLOv8 (`.onnx`) phát hiện người / vật thể trong vùng ROI
- 📐 **Cấu hình ROI linh hoạt** — định nghĩa vùng theo từng camera, lưu JSON
- 🚨 **Cảnh báo thời gian thực** — lưu ảnh bằng chứng, gửi WebSocket, Gmail, ERP
- 🗄️ **SQLite local** — `data/sentinel.db` (không commit, sinh runtime)
- 🐳 **Docker-ready** — `Dockerfile` + `docker-compose.yml` đi kèm
- 🔁 **CI/CD** — GitHub Actions cho deploy & build image

---

## 🏗️ Cấu trúc dự án

```
PERSON_HTMP/
├── HTMP_AI_Systems/          # Package chính
│   ├── app/                  # Flask app (routes, static, templates)
│   ├── core/                 # Config, logging, constants
│   ├── db/                   # SQLAlchemy models, repository, connection
│   ├── pipelines/            # Camera stream, AI worker, worker manager
│   ├── services/             # AI engine (YOLO inference)
│   ├── events/               # Event dispatcher
│   ├── integrations/         # ERP, Gmail, WebSocket
│   ├── scripts/              # DB migration, seed, utility
│   ├── docs/                 # Tài liệu kỹ thuật
│   ├── templates/            # Jinja2 templates (UI)
│   ├── .github/workflows/    # CI/CD pipelines
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── data/
│   └── roi_config_*.json     # Cấu hình ROI theo camera (commit)
└── README.md
```

> **Không commit**: `models/*.onnx`, `logs/`, `data/sentinel.db`, `data/violations/`, `backups/`, `scratch/`, `.env`, `.vscode/`

---

## 🚀 Cài đặt nhanh

### Yêu cầu
- Python ≥ 3.10
- (Tùy chọn) Docker + Docker Compose
- (Tùy chọn) GPU NVIDIA + CUDA cho inference nhanh

### Local
```bash
# Clone
git clone https://github.com/AnhMinhh12/PERSON_HTMP.git
cd PERSON_HTMP/HTMP_AI_Systems

# Tạo venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt

# Cấu hình
cp .env.example .env
# Sửa .env với thông tin ERP, Gmail, camera URL, ...

# Tải model (không commit do kích thước)
# Đặt yolov8s.onnx vào HTMP_AI_Systems/models/

# Chạy
python -m app.main
# hoặc: bash run.sh
```

### Docker
```bash
cd HTMP_AI_Systems
docker compose up -d
```

---

## ⚙️ Cấu hình

Mọi thông tin nhạy cảm lưu trong `.env` (tham khảo `.env.example`):

| Biến | Mô tả |
|------|--------|
| `CAMERA_URLS` | Danh sách URL camera (phân cách dấu phẩy) |
| `ERP_API_URL` | Endpoint ERP để đồng bộ vi phạm |
| `GMAIL_USER`, `GMAIL_APP_PASS` | Tài khoản gửi cảnh báo |
| `DATABASE_URL` | Connection string (mặc định SQLite) |
| `YOLO_MODEL_PATH` | Đường dẫn file `.onnx` |

---

## 📡 API & Sự kiện

- **HTTP API** — xem `app/routes.py`
- **WebSocket** — `/ws/events` (real-time violations)
- **ERP webhook** — tích hợp 2 chiều qua `integrations/erp.py`

Chi tiết tham khảo [HTMP_AI_Systems/docs/](HTMP_AI_Systems/docs/).

---

## 🧪 Testing

```bash
cd HTMP_AI_Systems
pytest tests/
```

---

## 📝 Tài liệu tham khảo

- [ARCHITECTURE.md](HTMP_AI_Systems/docs/ARCHITECTURE.md)
- [ROADMAP.md](HTMP_AI_Systems/docs/ROADMAP.md)
- [GPU_MIGRATION.md](HTMP_AI_Systems/docs/GPU_MIGRATION.md)
- [SERVER_SETUP_LOG.md](HTMP_AI_Systems/docs/SERVER_SETUP_LOG.md)

---

## 📄 License

Internal project — © 2026 AnhMinhh12.