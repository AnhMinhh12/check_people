# 🛡️ Sentinel Warden AI — Tài liệu Mô tả Hệ thống V5.0

> **Phiên bản**: V5.0 Enterprise Edition  
> **Cập nhật lần cuối**: 03/04/2026  
> **Repository**: [github.com/AnhMinhh12/check_people](https://github.com/AnhMinhh12/check_people)

---

## 📌 1. Giới thiệu Tổng quan

**Sentinel Warden AI** là hệ thống giám sát an toàn lao động sử dụng trí tuệ nhân tạo (AI), được thiết kế chuyên biệt cho môi trường dây chuyền sản xuất công nghiệp. Hệ thống hoạt động **24/7 liên tục**, tự động nhận diện công nhân qua camera RTSP và cảnh báo ngay lập tức khi phát hiện công nhân rời khỏi vị trí làm việc (Vùng An Toàn — ROI) quá thời gian quy định.

**Đặc điểm quan trọng**: Hệ thống AI chạy hoàn toàn **phía Server (Backend)**. Dù người giám sát đóng trình duyệt, chuyển tab, hay tắt màn hình — AI vẫn tiếp tục nhận diện và ghi log vi phạm liên tục.

---

## 🚀 2. Điểm Nổi bật Phiên bản V4.5

| # | Tính năng | Mô tả |
|---|---|---|
| 1 | **YOLOv8s (Small Model)** | Nâng cấp từ YOLOv8n (Nano) lên bản Small. Tăng độ chính xác đáng kể cho các tư thế khó: cúi người, quay lưng, đứng nghiêng |
| 2 | **Trí nhớ tạm (Persistence Buffer)** | Bộ đệm 5 khung hình — Khi AI bị mất dấu người đột ngột (do che khuất tạm thời), hệ thống giữ lại vị trí cũ thêm 5 frame, triệt tiêu hoàn toàn hiện tượng "nháy" Bounding Box |
| 3 | **Quét đa điểm dọc thân (Vertical Scan)** | Quét 5 điểm dọc cơ thể: Chân (1.0) → Đầu gối (0.8) → Hông (0.6) → Ngực (0.4) → Vai (0.2). Chỉ cần 1/5 điểm lọt vào ROI = AN TOÀN |
| 4 | **YOLO Built-in Tracker** | Sử dụng `model.track(persist=True)` để cấp ID duy nhất cho mỗi người. Kết hợp với Persistence Buffer để theo dõi chính xác từng cá nhân |
| 5 | **Chống đếm trùng (Custom NMS)** | Thuật toán lọc chồng lấn (IoU > 50%) tránh đếm 1 người thành 2 |
| 6 | **Bộ đệm trạng thái 1 giây** | Sau khi AI mất dấu, chờ thêm 1 giây xác nhận trước khi chuyển từ AN TOÀN → RỜI VỊ TRÍ. Tránh cảnh báo giả |
| 7 | **CI/CD Docker tự động** | Push code lên GitHub → Tự động Build Docker Image → Đẩy lên GitHub Container Registry |
| 8 | **Hướng dẫn vẽ ROI trên giao diện** | Tab Cấu hình hiển thị panel hướng dẫn 3 bước (Chuột trái chấm điểm, Chuột phải hoàn tác, Vẽ khép kín) |

---

## 🧠 3. Logic Vận hành Chi tiết

### 3.1 Luồng xử lý chính
```
Camera RTSP (30fps)
    │
    ▼
CameraStreamer Thread ──▶ Frame Buffer (Luôn giữ frame mới nhất)
    │
    ▼
AI Worker Thread (Đọc frame từ Buffer)
    │
    ├── 1) YOLOv8s Inference (detect + track)
    │       → Trả về: Tọa độ box + Track ID cho mỗi người
    │
    ├── 2) Persistence Buffer Check
    │       → Người vắng < 5 frame? Giữ lại vị trí cũ
    │       → Người vắng > 5 frame? Xóa khỏi bộ nhớ
    │
    ├── 3) Multi-point ROI Scan (5 điểm dọc thân)
    │       → Test 5 tỉ lệ: [1.0, 0.8, 0.6, 0.4, 0.2]
    │       → Bất kỳ điểm nào trong ROI? → is_safe = True
    │
    ├── 4) Custom NMS (Chống đếm trùng)
    │       → Sắp xếp box theo diện tích (lớn → nhỏ)
    │       → Loại bỏ box có IoU > 50% với box lớn hơn
    │
    └── 5) Trạng thái Vi phạm
            → count_in_roi < 1 → Bắt đầu đếm giây
            → < 1s: Giữ nguyên AN TOÀN (đệm chống nháy)
            → 1s–5s: Trạng thái RỜI VỊ TRÍ (thanh bar vàng)
            → ≥ 5s: Trạng thái VI PHẠM → Chụp ảnh, ghi DB
```

### 3.2 Trạng thái hệ thống

| Trạng thái | Điều kiện | Hiển thị Dashboard |
|---|---|---|
| **ĐANG CHỜ** | Vừa khởi động, chưa có dữ liệu | Chữ trắng |
| **AN TOÀN** | Có ít nhất 1 người trong ROI, hoặc vắng < 1s | Chữ xanh cyan, viền xanh |
| **RỜI VỊ TRÍ** | Vắng mặt từ 1s đến 5s | Chữ cam, thanh bar đỏ chạy |
| **VI PHẠM** | Vắng mặt ≥ 5s | Chữ đỏ, HUD toàn màn hình đỏ nhấp nháy |

### 3.3 Ghi bằng chứng vi phạm
Khi trạng thái chuyển sang **VI PHẠM** (≥ 5s), hệ thống tự động:
1. Chụp ảnh frame hiện tại kèm các Bounding Box và đường viền ROI (Annotated Image).
2. Đóng dấu chữ `"VI PHAM DANG DIEN RA"` lên ảnh.
3. Lưu vào thư mục `violations/` với tên `violation_YYYYMMDD_HHMMSS.jpg`.
4. Khi công nhân quay lại vị trí → Ghi tổng thời gian vắng mặt vào Database SQLite.

---

## 🛠️ 4. Yêu cầu Hệ thống Hiện tại

| Hạng mục | Yêu cầu tối thiểu | Khuyến nghị |
|---|---|---|
| **CPU** | Intel Core i5 Gen 10+ | Intel Core i7 Gen 13 (i7-1355U) |
| **RAM** | 8 GB | 16 GB |
| **Ổ cứng** | SSD 256GB | SSD 512GB |
| **Mạng** | WiFi (dùng tạm) | **Cáp LAN Ethernet** (bắt buộc cho sản xuất) |
| **Camera** | IP Camera hỗ trợ RTSP | Hikvision / Dahua (đã test thực tế) |
| **OS** | Windows 10/11, Ubuntu 20.04+ | Windows 11 + Docker Desktop |
| **Python** | 3.10+ | 3.11 |

---

## 📊 5. Cấu trúc Thư mục Dự án

```
check_person/
├── app.py                          # Entry point — Khởi tạo Flask + SocketIO + Worker
├── .env                            # Cấu hình: RTSP URL, Model Path, Data paths...
├── requirements.txt                # Thư viện Python (Flask, YOLO, OpenCV...)
├── Dockerfile                      
├── docker-compose.yml              
│
├── src/                            # Mã nguồn chính
│   ├── core/
│   │   ├── ai_engine.py            # AI Engine
│   │   ├── camera_stream.py        # Streamer
│   │   └── database.py             # Database Manager V5.0
│   ├── services/
│   │   └── ai_worker.py            # AI Worker Logic & Logging tách biệt
│   └── api/
│       └── routes.py               # REST API endpoints
│
├── data/                           # Dữ liệu động (DB, ROI, Violations)
│   ├── sentinel.db        
│   ├── roi_config_*.json  
│   └── violations/                 # Ảnh bằng chứng vi phạm
│
├── models/                         # Mô hình AI (.pt)
│
├── logs/                           # Nhật ký hoạt động từng Camera
│
└── docs/                           # Tài liệu hệ thống
```

---

## 🔧 6. Cấu hình Hệ thống

### 6.1 File `.env`
```env
RTSP_URL=rtsp://admin:password@ip_address:554/stream
FLASK_PORT=5000
FLASK_DEBUG=False
MODEL_PATH=yolov8s.pt
CONFIDENCE_THRESHOLD=0.15
ALARM_DELAY_SECONDS=5.0
```

### 6.2 Các thông số quan trọng trong code

| Thông số | Giá trị | Vị trí | Ý nghĩa |
|---|---|---|---|
| `CONFIDENCE_THRESHOLD` | `0.15` | `.env` + `ai_engine.py` | Ngưỡng tin cậy tối thiểu để AI xác nhận "đây là người". Thấp = nhạy hơn nhưng dễ báo nhầm |
| `max_memory_frames` | `5` | `ai_engine.py` dòng 33 | Số frame giữ vết khi mất dấu người (chống nháy). Tăng = ổn định hơn nhưng phản ứng chậm hơn |
| `alarm_delay` | `5.0` | `app.py` dòng 21 | Số giây vắng mặt trước khi ghi nhận VI PHẠM |
| Bộ đệm trạng thái | `1.0` giây | `ai_worker.py` dòng 76 | Thời gian chờ xác nhận sau khi mất dấu. Dưới 1s = vẫn AN TOÀN |
| Dashboard emit rate | `0.2` giây (5Hz) | `ai_worker.py` dòng 98 | Tần suất gửi dữ liệu real-time lên Web Dashboard |
| JPEG Quality | `50` | `ai_worker.py` dòng 102 | Chất lượng ảnh truyền lên Dashboard (cân bằng nét/nhanh) |
| ROI Scale | `640x360` | `ai_engine.py` dòng 62 | Tọa độ ROI trên Web được scale lên kích thước thực của Camera |

---

## 📡 7. API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/` | Trang Dashboard chính |
| `GET` | `/api/history` | Lấy 50 vi phạm gần nhất (JSON) |
| `GET` | `/api/health` | Kiểm tra sức khỏe hệ thống (`{"status": "ok"}`) |
| `POST` | `/api/config_roi` | Lưu tọa độ ROI mới (`{"points": [[x,y], ...]}`) |
| `GET` | `/violations/<filename>` | Truy cập ảnh bằng chứng vi phạm |
| WebSocket | `stats_update` | Sự kiện real-time: Trạng thái, FPS, ảnh live, tọa độ người, ROI |

---

## 🐋 8. Thông tin CI/CD & Docker

### 8.1 GitHub Actions Workflow
- **Trigger**: Mỗi lần `git push` lên nhánh `main` hoặc `master`
- **Quy trình**: Checkout → Login GHCR → Build Docker Image → Push lên `ghcr.io`
- **Không chạy Unit Test trên CI** (đã tối giản để đảm bảo Build luôn thành công)

### 8.2 Docker Image
- **Base**: `python:3.11-slim`
- **Thư viện hệ thống**: `libgl1`, `libglib2.0-0`, `libsm6`, `libxext6`, `curl`
- **PyTorch**: Bản CPU-only (giảm kích thước Image)
- **Registry**: `ghcr.io/anhminhh12/check_people:main`

### 8.3 Dependencies (requirements.txt)
```
Flask==2.2.5
Flask-SocketIO==5.3.4
numpy<2.0.0
ultralytics
python-dotenv==1.0.0
eventlet==0.33.3
opencv-python-headless
```

---

*Tài liệu được tạo tự động từ trạng thái code thực tế ngày 01/04/2026*