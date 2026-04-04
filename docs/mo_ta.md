# 🛡️ Sentinel Warden AI — Tài liệu Mô tả Hệ thống V5.5

> **Phiên bản**: V5.5 Enterprise Edition (Optimized ONNX)  
> **Cập nhật lần cuối**: 04/04/2026  
> **Repository**: [github.com/AnhMinhh12/check_people](https://github.com/AnhMinhh12/check_people)

---

## 📌 1. Giới thiệu Tổng quan

AI vẫn tiếp tục nhận diện và ghi bản ghi vi phạm liên tục.

### 2. Quản lý Đa Camera (Multi-Camera Manager)
V5.0 giới thiệu khả năng quản lý động danh sách camera qua biến môi trường:
- **Quét biến môi trường**: Tự động nhận diện cặp `RTSP_URL{i}` và `CAMERA_NAME{i}` (từ i=1 đến 100).
- **Auto-Sync**: Tự động thêm camera mới vào DB hoặc cập nhật tên camera nếu link RTSP cũ đã tồn tại.
- **Hard Delete (Dọn dẹp)**: Xóa vĩnh viễn các camera trong DB không có khai báo trong `.env` để bảo đảm Dashboard luôn sạch sẽ.

### 3. Log vi phạm (Violation Logging)

---

## 🚀 2. Điểm Nổi bật Phiên bản V5.0 Enterprise

| # | Tính năng | Mô tả |
|---|---|---|
| 1 | **YOLOv8s & Shared Model Memory** | Nạp model AI 1 lần duy nhất tại WorkerManager và chia sẻ cho toàn bộ camera, tối ưu hóa RAM tối đa. Nâng cấp lên bản YOLOv8s tăng xác suất nhận diện tư thế khó. |
| 2 | **Trí nhớ tạm (Persistence Buffer)** | Bộ đệm 5 khung hình — Khi AI bị mất dấu người đột ngột (do che khuất tạm thời), hệ thống giữ lại vị trí cũ thêm 5 frame, triệt tiêu hoàn toàn hiện tượng "nháy" Bounding Box |
| 3 | **Cơ chế Mask Overlap** | Thuật toán quét điểm ảnh dựa trên Mask của ROI (điền bởi cv2.fillPoly) thay cho kiểm tra hộp điểm, nhanh chóng xác định chính xác sự chồng lấn với vùng an toàn. |
| 4 | **YOLO Built-in Tracker** | Sử dụng `model.track(persist=True)` để cấp ID duy nhất cho mỗi người. Kết hợp với Persistence Buffer để theo dõi chính xác từng cá nhân |
| 5 | **Chống đếm trùng (Custom NMS)** | Thuật toán lọc chồng lấn (IoU > 50%) tránh đếm 1 người thành 2 |
| 6 | **Bộ đệm trạng thái 1 giây** | Sau khi AI mất dấu, chờ thêm 1 giây xác nhận trước khi chuyển từ AN TOÀN → RỜI VỊ TRÍ. Tránh cảnh báo giả |
| 7 | **CI/CD Docker tự động** | Push code lên GitHub → Tự động Build Docker Image → Đẩy lên GitHub Container Registry |
| 8 | **Hướng dẫn vẽ ROI trên giao diện** | Tab Cấu hình hiển thị panel hướng dẫn 3 bước (Chuột trái chấm điểm, Chuột phải hoàn tác, Vẽ khép kín) |
| 9 | **UI/UX Typography Inter** | Giao diện sử dụng font Inter chuẩn Enterprise, terminology tối ưu và localize thành tiếng Việt chuẩn thống nhất |
| 10| **AI Frame Skipping (Optimization)** | V5.1 giới hạn số lần gọi AI Model giúp giảm tải CPU/GPU lên tới 70% |
| 11| **Preprocessing Optimization** | V5.2 thực hiện Resize 1 lần duy nhất cho AI và Web, giảm tải RAM và CPU đáng kể |
| 12| **ONNX Engine (Acceleration)** | V5.3 chuyển sang định dạng ONNX tối ưu thay thế PyTorch nguyên bản, giúp cải thiện tốc độ xử lý FPS đáng kể trên CPU. |

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
    ├── 3) Mask Overlap Scan (Chồng lấn điểm ảnh)
    │       → Sinh Mask của ROI tại kích thước thực qua cv2.fillPoly
    │       → np.any(box_roi == 255) → Bất kỳ điểm ảnh nào trong box chạm ROI? → is_safe = True
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
│   │   ├── database.py             # Database Manager V5.0
│   │   └── worker_manager.py       # Quản lý AI Worker và Share Model (Tối ưu RAM)
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
├── models/                         # Mô hình AI đã tối ưu
│   └── yolov8s.onnx                # Phiên bản ONNX Runtime (45MB)
│
├── logs/                           # Nhật ký hoạt động từng Camera
│
└── docs/                           # Tài liệu hệ thống
```

---

## 🔧 6. Cấu hình Hệ thống

### 6.1 File `.env`
```env
# Cấu hình cụm Camera
RTSP_URL1=rtsp://admin:password@192.168.1.10:554/stream
CAMERA_NAME1=Máy Hàn 01

RTSP_URL2=rtsp://admin:password@192.168.1.11:554/stream
CAMERA_NAME2=Khu Vực Bốc Xếp

# Thông số AI
MODEL_PATH=models/yolov8s.onnx
CONFIDENCE_THRESHOLD=0.15
ALARM_DELAY_SECONDS=5.0
AI_MAX_FPS=10
FLASK_DEBUG=False
```

### 6.2 Các thông số quan trọng

| Thông số | Giá trị | Vị trí | Ý nghĩa |
|---|---|---|---|
| `RTSP_URL{i}` | `...` | `.env` | Link stream RTSP của Cam thứ i |
| `CAMERA_NAME{i}` | `...` | `.env` | Tên hiển thị của Cam thứ i |
| `CONFIDENCE_THRESHOLD` | `0.15` | `.env` | Ngưỡng tin cậy tối thiểu của AI |
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
| `GET` | `/api/history` | Lấy 50 vi phạm gần nhất (Bao gồm `camera_name`) |
| `GET` | `/api/health` | Kiểm tra sức khỏe hệ thống |
| `POST` | `/api/config_roi` | Lưu tọa độ ROI mới theo `camera_id` |
| `GET` | `/violations/<filename>` | Truy cập ảnh bằng chứng |
| `WebSocket` | `stats_update_{id}` | Luồng dữ liệu real-time riêng cho từng Camera |

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
Flask==2.3.3
Flask-SocketIO==5.3.6
numpy<2.0.0
ultralytics>=8.3.0
python-dotenv==1.0.1
eventlet==0.33.3
opencv-python-headless>=4.8.0
onnxruntime>=1.15.0
lapx>=0.5.5
```

---

*Tài liệu được tạo tự động từ trạng thái code thực tế ngày 01/04/2026*