# 🗺️ Lộ trình Phát triển & Kế hoạch Mở rộng — Sentinel Warden AI

> **Phiên bản hiện tại**: V5.0 (Enterprise Edition)  
> **Ngày cập nhật**: 03/04/2026  
> **Trạng thái**: Đã hoàn thành tải cấu trúc dự án. Đang vận hành ổn định mô hình Đa Camera.

---

## 📋 Mục lục

1. [Đánh giá Hiện trạng](#-1-đánh-giá-hiện-trạng-hệ-thống-v50)
2. [Kế hoạch Mở rộng Camera](#-2-kế-hoạch-mở-rộng-camera)
3. [Nâng cấp Phần cứng (Server)](#-3-nâng-cấp-phần-cứng-server)
4. [Cải thiện Phần mềm](#-4-cải-thiện-phần-mềm)
5. [Nâng cấp Giao diện Dashboard](#-5-nâng-cấp-giao-diện-dashboard)
6. [Bảo mật & Quản trị](#-6-bảo-mật--quản-trị)
7. [Tích hợp Hệ thống Bên ngoài](#-7-tích-hợp-hệ-thống-bên-ngoài)
8. [Lộ trình Theo giai đoạn](#-8-lộ-trình-theo-giai-đoạn)
9. [Ước tính Chi phí](#-9-ước-tính-chi-phí)

---

## 🔍 1. Đánh giá Hiện trạng Hệ thống V5.0

### 1.1 Những gì đã hoàn thành ✅
| Tính năng | Trạng thái | Ghi chú |
|---|---|---|
| Nhận diện người (YOLOv8s) | ✅ Hoàn thành | Độ chính xác cao, chạy trên CPU i7 Gen 13 |
| Quét đa điểm dọc thân (5 điểm) | ✅ Hoàn thành | Từ chân lên vai, bao phủ mọi tư thế |
| Bộ nhớ đệm chống nháy (Persistence) | ✅ Hoàn thành | Giữ vết 5 khung hình, loại bỏ "ghost box" |
| Vẽ vùng an toàn ROI trên Web | ✅ Hoàn thành | Đa giác tùy chỉnh, chuột trái/phải |
| Cảnh báo HUD toàn màn hình | ✅ Hoàn thành | Viền đỏ nhấp nháy khi vi phạm |
| Hỗ trợ nhiều Camera (Mới V4.5) | ✅ Hoàn thành | Chạy đa luồng song song |
| Giao diện Grid Dashboard (Mới V4.5) | ✅ Hoàn thành | Lưới tổng quan và trang xem chi tiết |
| Quy hoạch cấu trúc Enterprise (Mới V5.0)| ✅ Hoàn thành | Tách biệt Source (`src/`), Database (`data/`), Model (`models/`) |

### 1.2 Hạn chế hiện tại ⚠️
| Hạn chế | Mức độ | Ảnh hưởng |
|---|---|---|
| Chỉ hỗ trợ 1 Camera duy nhất | 🔴 Nghiêm trọng | Không giám sát được nhiều vị trí |
| Chạy trên CPU (không có GPU) | 🟡 Trung bình | FPS bị giới hạn ở mức 10-15 |
| Database SQLite (đơn luồng) | 🟡 Trung bình | Không phù hợp khi có >10 camera ghi đồng thời |
| Không có hệ thống phân quyền | 🟡 Trung bình | Ai cũng có thể truy cập Dashboard |
| Không có thông báo đẩy (Push Notification) | 🟠 Nhẹ | Phải ngồi trực Dashboard mới biết vi phạm |
| Chưa có báo cáo thống kê tự động | 🟠 Nhẹ | Dữ liệu tab Phân Tích đang là mẫu cứng |
| Phụ thuộc WiFi (không ổn định) | 🟡 Trung bình | Frame Freeze khi mạng yếu |

---

## 📷 2. Kế hoạch Mở rộng Camera

### 2.1 Giai đoạn 1: Lên 5 Camera (Ngắn hạn)
**Mục tiêu**: Giám sát 5 vị trí làm việc trên cùng một dây chuyền sản xuất.

**Thay đổi cần thực hiện**:
- **Kiến trúc Multi-Camera Worker**: Mỗi camera sẽ là một tiến trình (Process) độc lập, chạy song song trên cùng một máy chủ.
  ```
  app.py
  ├── CameraWorker #1 (Camera Vị trí 1 - RTSP://192.168.1.10)
  ├── CameraWorker #2 (Camera Vị trí 2 - RTSP://192.168.1.11)
  ├── CameraWorker #3 (Camera Vị trí 3 - RTSP://192.168.1.12)
  ├── CameraWorker #4 (Camera Vị trí 4 - RTSP://192.168.1.13)
  └── CameraWorker #5 (Camera Vị trí 5 - RTSP://192.168.1.14)
  ```
- **Cấu hình động (Dynamic Config)**: File `.env` hoặc `config.yaml` sẽ chứa danh sách camera thay vì hardcode 1 URL duy nhất.
  ```yaml
  cameras:
    - id: cam_01
      name: "Dây chuyền A - Vị trí 1"
      rtsp_url: "rtsp://admin:pass@192.168.1.10:554/stream"
      roi_config: "roi_cam01.json"
    - id: cam_02
      name: "Dây chuyền A - Vị trí 2"
      rtsp_url: "rtsp://admin:pass@192.168.1.11:554/stream"
      roi_config: "roi_cam02.json"
  ```
- **Dashboard Grid View**: Giao diện Web sẽ hiển thị lưới 2x3 hoặc 3x2, mỗi ô là một camera live.

**Yêu cầu phần cứng**: Intel Core i7/i9 Gen 13+ hoặc AMD Ryzen 7/9 với RAM 32GB.

### 2.2 Giai đoạn 2: Lên 20 Camera (Trung hạn)
**Mục tiêu**: Giám sát toàn bộ một phân xưởng sản xuất.

**Thay đổi cần thực hiện**:
- **Chuyển sang GPU Server**: Máy chủ trang bị NVIDIA RTX 4070/4090 hoặc Tesla T4.
  - Mỗi card GPU có thể xử lý 15-20 luồng camera đồng thời ở mức 25+ FPS.
- **Docker Swarm / Kubernetes**: Mỗi camera là một Container Docker riêng biệt.
  ```yaml
  # docker-compose.yml (Multi-camera)
  services:
    warden-cam01:
      image: ghcr.io/anhminhh12/check_people:main
      environment:
        - CAMERA_ID=cam_01
        - RTSP_URL=rtsp://192.168.1.10/stream
      deploy:
        resources:
          reservations:
            devices:
              - capabilities: [gpu]
    warden-cam02:
      image: ghcr.io/anhminhh12/check_people:main
      environment:
        - CAMERA_ID=cam_02
        - RTSP_URL=rtsp://192.168.1.11/stream
  ```
- **Message Queue (Redis/RabbitMQ)**: Các Camera Worker sẽ gửi kết quả nhận diện qua hàng đợi tin nhắn (Message Queue) thay vì ghi trực tiếp vào database. Điều này giúp hệ thống không bị nghẽn khi 20 camera cùng phát hiện vi phạm đồng thời.
- **Database PostgreSQL**: Chuyển từ SQLite sang PostgreSQL để hỗ trợ ghi đồng thời từ nhiều nguồn.

**Yêu cầu phần cứng**: 
- Server có 1-2x GPU NVIDIA (16GB VRAM mỗi card)
- RAM: 64GB
- SSD: 1TB (lưu trữ ảnh vi phạm)
- Mạng: Switch Gigabit Ethernet

### 2.3 Giai đoạn 3: Lên 50-100 Camera (Dài hạn)
**Mục tiêu**: Giám sát toàn bộ nhà máy, nhiều phân xưởng, nhiều tầng.

**Kiến trúc Phân tán (Distributed Architecture)**:
```
                    ┌──────────────────────┐
                    │   CENTRAL DASHBOARD  │
                    │   (Web Portal)       │
                    │   PostgreSQL + Redis │
                    └──────┬───────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │  EDGE #1  │   │  EDGE #2  │   │  EDGE #3  │
    │ GPU Server│   │ GPU Server│   │ GPU Server│
    │ 20 Camera │   │ 20 Camera │   │ 20 Camera │
    └───────────┘   └───────────┘   └───────────┘
```

**Thay đổi cần thực hiện**:
- **Central Dashboard**: Một trang Web duy nhất tổng hợp dữ liệu từ tất cả các Edge Server. Quản lý có thể xem toàn cảnh nhà máy từ một màn hình.
- **Edge Computing**: Mỗi phân xưởng có một Server riêng (Edge Node) xử lý 15-20 camera cục bộ, giảm tải hệ thống mạng trung tâm.
- **Load Balancing (Nginx/HAProxy)**: Phân phối traffic đều giữa các Edge Server. Nếu một Server bị sập, camera tự động được chuyển sang Server dự phòng.
- **Object Storage (MinIO/S3)**: Lưu trữ ảnh bằng chứng vi phạm trên hệ thống lưu trữ đối tượng phân tán, thay vì lưu cục bộ trên ổ cứng Server.

---

## 🖥️ 3. Nâng cấp Phần cứng (Server)

### 3.1 Cấu hình Server khuyến nghị theo quy mô

| Thông số | 5 Camera | 20 Camera | 50-100 Camera |
|---|---|---|---|
| **CPU** | Intel i7 Gen 13 | Xeon W hoặc EPYC | 2x Xeon hoặc EPYC |
| **RAM** | 32 GB | 64 GB | 128 GB |
| **GPU** | Không bắt buộc | 1x RTX 4090 (24GB) | 2-4x RTX 4090 hoặc A100 |
| **Ổ cứng** | SSD 512GB | SSD 1TB NVMe | RAID SSD 2-4TB |
| **Mạng** | Gigabit LAN | 10Gbps LAN | 10Gbps + Switch PoE |
| **Dự phòng** | Không | UPS 1h | UPS + Server dự phòng |

### 3.2 Card GPU so sánh chi tiết

| Card GPU | VRAM | Số camera xử lý được | FPS mỗi camera | Giá tham khảo |
|---|---|---|---|---|
| NVIDIA RTX 4070 | 12 GB | 8-12 camera | 30+ FPS | ~15 triệu VNĐ |
| NVIDIA RTX 4090 | 24 GB | 15-25 camera | 50+ FPS | ~45 triệu VNĐ |
| NVIDIA Tesla T4 | 16 GB | 12-18 camera | 40+ FPS | ~25 triệu VNĐ |
| NVIDIA A100 | 40/80 GB | 30-50 camera | 60+ FPS | ~200 triệu VNĐ |

> **Khuyến nghị**: Với ngân sách tối ưu, chọn **RTX 4090** vì tỉ lệ hiệu năng/giá thành là tốt nhất cho dự án này.

### 3.3 Hạ tầng Mạng
- **Bắt buộc**: Chuyển toàn bộ camera và Server sang **cáp mạng LAN (Ethernet)**. WiFi tuyệt đối không nên sử dụng cho hệ thống giám sát an toàn công nghiệp.
- **Switch PoE (Power over Ethernet)**: Cấp nguồn trực tiếp cho camera qua dây mạng, giảm thiểu dây điện và tăng độ tin cậy.
- **VLAN riêng biệt**: Tách riêng mạng camera giám sát khỏi mạng văn phòng/internet để đảm bảo băng thông và bảo mật.

---

## 💻 4. Cải thiện Phần mềm

### 4.1 Nâng cao AI Engine (Ưu tiên Cao 🔴)

#### a) Tích hợp GPU Acceleration (CUDA/TensorRT)
- **Hiện tại**: AI chạy trên CPU bằng PyTorch thuần. Tốc độ bị giới hạn ở mức 10-15 FPS.
- **Cải thiện**: Khi có Server GPU, chuyển sang sử dụng **TensorRT** (thư viện tối ưu AI của NVIDIA).
  - Tốc độ dự kiến tăng từ **15 FPS lên 80-120 FPS**.
  - Chỉ cần thay đổi 1 dòng code trong `ai_engine.py`:
    ```python
    # Hiện tại
    self.model = YOLO("yolov8s.pt")
    # Sau khi có GPU
    self.model = YOLO("yolov8s.engine")  # TensorRT optimized
    ```

#### b) Kalman Filter Tracking (Bộ lọc Kalman)
- **Hiện tại**: Hệ thống sử dụng Persistence Buffer (đệm 5 frame) để chống nháy.
- **Cải thiện**: Tích hợp **Kalman Filter** để dự đoán vị trí tiếp theo của công nhân dựa trên quỹ đạo di chuyển.
  - Lợi ích: Bounding Box sẽ di chuyển cực mượt mà, không bao giờ bị "nhảy" vị trí.
  - Thư viện: `filterpy` hoặc tích hợp sẵn trong `ultralytics` (ByteTrack/BoTSORT).

#### c) Nhận diện Hành vi (Action Recognition)
- **Hiện tại**: AI chỉ biết "CÓ NGƯỜI" hay "KHÔNG CÓ NGƯỜI".
- **Cải thiện**: Mở rộng khả năng nhận diện hành vi cụ thể:
  - Đang đứng làm việc ✅
  - Đang ngồi nghỉ ⚠️
  - Đang nằm (ngã) 🚨
  - Đang sử dụng điện thoại ⚠️
  - Không đội mũ bảo hộ 🚨
- **Công nghệ**: Sử dụng thêm model phụ (YOLOv8-Pose cho xương người, hoặc custom-trained model cho PPE detection).

#### d) Hỗ trợ OpenVINO cho Intel GPU
- **Hiện tại**: Đã thử export nhưng gặp lỗi `Attribute and shape size inconsistent`.
- **Cải thiện**: Khi Ultralytics cập nhật phiên bản mới hơn, thử lại việc export sang OpenVINO để tận dụng Intel iGPU (Iris Xe) trên chip i7 Gen 13.
  - Dự kiến tăng FPS từ 15 lên 25-30 mà không cần card GPU rời.

### 4.2 Cải thiện Camera Stream (Ưu tiên Cao 🔴)

#### a) Reconnect Tự động (Auto-Reconnect)
- **Hiện tại**: Khi camera mất kết nối, hệ thống chỉ hiện **"MẤT TÍN HIỆU"** và chờ.
- **Cải thiện**: Tự động thử kết nối lại sau mỗi 5 giây (tối đa 10 lần). Nếu vẫn thất bại, gửi cảnh báo qua Email/Telegram.
  ```python
  class CameraStreamer:
      def reconnect(self):
          for attempt in range(10):
              self.cap = cv2.VideoCapture(self.rtsp_url)
              if self.cap.isOpened():
                  logger.info(f"Kết nối lại Camera thành công (Lần {attempt+1})")
                  return True
              time.sleep(5)
          self.send_alert("Camera hoàn toàn mất tín hiệu!")
          return False
  ```

#### b) Health Check & Watchdog
- **Hiện tại**: Không có cơ chế giám sát sức khỏe hệ thống.
- **Cải thiện**: 
  - Kiểm tra FPS mỗi 30 giây. Nếu FPS < 3 liên tục trong 2 phút → Cảnh báo "Hệ thống đang quá tải".
  - Kiểm tra dung lượng ổ cứng. Nếu < 1GB trống → Tự động xóa ảnh vi phạm cũ nhất (>30 ngày).
  - API Endpoint `/api/health` trả về trạng thái toàn bộ hệ thống (đã có sẵn, cần mở rộng thêm thông tin).

### 4.3 Cải thiện Database & Lưu trữ (Ưu tiên Trung bình 🟡)

#### a) Chuyển đổi sang PostgreSQL
- **Hiện tại**: SQLite - đơn giản nhưng chỉ hỗ trợ 1 kết nối ghi tại một thời điểm.
- **Cải thiện**: PostgreSQL cho phép hàng trăm kết nối đồng thời, phù hợp với kiến trúc đa camera.
  - Sử dụng **Docker Container riêng** cho PostgreSQL.
  - Tích hợp **SQLAlchemy ORM** để code không cần thay đổi nhiều khi chuyển database.

#### b) Hệ thống Sao lưu Tự động (Backup)
- Sao lưu database mỗi ngày vào một thư mục riêng hoặc đẩy lên Cloud (Google Drive / OneDrive).
- Lưu giữ ảnh vi phạm tối đa 90 ngày, sau đó tự động nén (ZIP) và lưu trữ dài hạn.

#### c) Tìm kiếm & Lọc Nâng cao
- Cho phép tìm kiếm vi phạm theo:
  - Khoảng thời gian (từ ngày ... đến ngày ...)
  - Theo camera cụ thể
  - Theo mức độ nghiêm trọng (> 10 giây, > 30 giây, > 1 phút)
- Xuất báo cáo Excel/PDF tự động theo tuần/tháng.

---

## 🎨 5. Nâng cấp Giao diện Dashboard

### 5.1 Grid View Đa Camera (Ưu tiên Cao 🔴)
- Hiển thị **lưới camera** (2x2, 3x3, 4x4) trên một trang duy nhất.
- Mỗi ô có trạng thái riêng (xanh = an toàn, đỏ = vi phạm).
- Click vào một camera để phóng to toàn màn hình (Fullscreen Mode).

### 5.2 Tab Phân Tích Thực tế (Ưu tiên Trung bình 🟡)
- **Hiện tại**: Tab "Phân Tích" đang hiển thị dữ liệu cứng (98.5%, 0h14m, 12 lần).
- **Cải thiện**: Kết nối dữ liệu thực từ Database:
  - Biểu đồ cột theo ngày trong tuần (dữ liệu thực).
  - Tỉ lệ trực vị trí = (Tổng giờ giám sát - Tổng giờ vắng mặt) / Tổng giờ giám sát × 100%.
  - So sánh xu hướng vi phạm giữa các tuần.
  - Sử dụng thư viện **Chart.js** hoặc **ApexCharts** để vẽ biểu đồ động.

### 5.3 Bản đồ Nhà máy (Factory Floor Map) (Ưu tiên Thấp 🟢)
- Upload sơ đồ mặt bằng nhà máy (ảnh 2D).
- Đặt các biểu tượng camera lên bản đồ theo vị trí thực tế.
- Khi có vi phạm, biểu tượng camera tương ứng sẽ nhấp nháy đỏ trên bản đồ.

### 5.4 Mobile Responsive (Ưu tiên Trung bình 🟡)
- Tối ưu giao diện cho điện thoại và máy tính bảng.
- Cho phép quản đốc kiểm tra trạng thái trên điện thoại khi đang đi kiểm tra phân xưởng.

---

## 🔒 6. Bảo mật & Quản trị

### 6.1 Đăng nhập & Phân quyền (Ưu tiên Cao 🔴)
- **Hiện tại**: Hệ thống có cơ chế đăng nhập cơ bản nhưng chưa phân quyền.
- **Cải thiện**:
  - **Admin**: Toàn quyền (Cấu hình ROI, quản lý camera, xem báo cáo, xóa dữ liệu).
  - **Supervisor (Quản đốc)**: Xem Dashboard, xem nhật ký vi phạm, xuất báo cáo.
  - **Viewer (Nhân viên)**: Chỉ xem Dashboard (không chỉnh sửa bất cứ thứ gì).
- Sử dụng **JWT Token** hoặc **Flask-Login** với session bảo mật.

### 6.2 HTTPS & Mã hóa Dữ liệu
- Bổ sung chứng chỉ SSL/TLS (Let's Encrypt miễn phí) để mã hóa toàn bộ giao tiếp giữa trình duyệt và Server.
- Mã hóa mật khẩu trong Database bằng **bcrypt**.

### 6.3 Audit Log (Nhật ký Kiểm toán)
- Ghi lại mọi hành động của người dùng: Ai đã đăng nhập, ai đã thay đổi ROI, ai đã xóa dữ liệu.
- Phục vụ cho việc kiểm toán nội bộ và đảm bảo tuân thủ quy trình ISO.

---

## 🔗 7. Tích hợp Hệ thống Bên ngoài

### 7.1 Cảnh báo Đẩy (Push Notification)
| Kênh | Mô tả | Ưu tiên |
|---|---|---|
| **Telegram Bot** | Gửi ảnh vi phạm + thông tin kèm link đến nhóm quản lý | 🔴 Cao |
| **Email (SMTP)** | Gửi báo cáo tổng hợp cuối ngày/tuần cho ban giám đốc | 🟡 Trung bình |
| **Loa / Còi cảnh báo** | Kích hoạt còi báo động vật lý khi phát hiện vi phạm nghiêm trọng | 🟡 Trung bình |
| **Zalo OA** | Thông báo qua API Zalo Official Account | 🟢 Thấp |

### 7.2 Tích hợp ERP / MES
- Đẩy dữ liệu vi phạm sang hệ thống quản lý sản xuất (MES) để tính toán OEE (Overall Equipment Effectiveness).
- Tích hợp với hệ thống chấm công để đối chiếu thời gian rời vị trí với thời gian nghỉ phép.

### 7.3 API RESTful Mở rộng
- Cung cấp API chuẩn REST để các hệ thống khác có thể:
  - Lấy danh sách vi phạm (`GET /api/violations`)
  - Lấy trạng thái camera (`GET /api/cameras/status`)
  - Cấu hình ROI từ xa (`POST /api/cameras/{id}/roi`)
  - Lấy thống kê tổng hợp (`GET /api/analytics/weekly`)

---

## 📅 8. Lộ trình Theo giai đoạn

### Phase 1 — Ổn định & Hoàn thiện (1-2 tháng)
- [ ] Tích hợp Auto-Reconnect cho Camera (Tự kết nối lại khi mất tín hiệu)
- [ ] Kết nối dữ liệu thực cho tab Phân Tích (Chart.js)
- [ ] Thêm Telegram Bot cảnh báo vi phạm
- [ ] Bổ sung tính năng tìm kiếm/lọc nhật ký vi phạm
- [ ] Tối ưu OpenVINO cho Intel iGPU (thử lại khi Ultralytics cập nhật)

### Phase 2 — Mở rộng Đa Camera (2-4 tháng)
- [ ] Thiết kế kiến trúc Multi-Camera Worker
- [ ] Xây dựng Dashboard Grid View (lưới đa camera)
- [ ] Chuyển Database sang PostgreSQL
- [ ] Tích hợp hệ thống phân quyền (Admin/Supervisor/Viewer)
- [ ] Triển khai trên Server có GPU (Docker + CUDA)

### Phase 3 — Nâng cấp Trí tuệ (4-6 tháng)
- [ ] Tích hợp Kalman Filter Tracking
- [ ] Thêm nhận diện trang bị bảo hộ (Mũ, Áo, Găng tay)
- [ ] Xây dựng bản đồ nhà máy (Factory Floor Map)
- [ ] Báo cáo tự động Excel/PDF gửi qua Email hàng tuần
- [ ] Tích hợp API ERP/MES

### Phase 4 — Quy mô Công nghiệp (6-12 tháng)
- [ ] Kiến trúc phân tán Edge Computing (50-100 camera)
- [ ] Load Balancing + High Availability (không bao giờ sập)
- [ ] Object Storage cho ảnh vi phạm (MinIO/S3)
- [ ] Mobile App (Android/iOS) cho quản đốc
- [ ] Nhận diện hành vi nâng cao (ngã, ngủ gật, sử dụng điện thoại)

---

## 💰 9. Ước tính Chi phí

### 9.1 Chi phí Phần cứng (Tham khảo)

| Hạng mục | Quy mô 5 Cam | Quy mô 20 Cam | Quy mô 100 Cam |
|---|---|---|---|
| Server (CPU + RAM + SSD) | 25-35 triệu | 60-80 triệu | 150-250 triệu |
| Card GPU (NVIDIA) | Không cần | 45-50 triệu (1x 4090) | 180-200 triệu (4x 4090) |
| Switch mạng PoE | 3-5 triệu | 8-15 triệu | 30-50 triệu |
| UPS dự phòng | 5 triệu | 10-15 triệu | 25-40 triệu |
| Cáp mạng CAT6 | 1-2 triệu | 5-8 triệu | 15-25 triệu |
| **Tổng ước tính** | **~40 triệu** | **~150 triệu** | **~500 triệu** |

### 9.2 Chi phí Phần mềm
- **Hiện tại**: **0 đồng** (Toàn bộ sử dụng mã nguồn mở: Python, YOLO, Flask, Docker).
- **Tương lai**: Có thể phát sinh chi phí cho các dịch vụ Cloud (nếu cần lưu trữ trên Cloud) hoặc license GPU Enterprise.

> ⚠️ **Lưu ý**: Các mức giá trên chỉ là ước tính tham khảo tại thời điểm 2026 và có thể thay đổi tùy theo thị trường và nhà cung cấp.

---

## 📝 Ghi chú cuối

Dự án **Sentinel Warden AI** đã đạt được nền tảng vững chắc tại phiên bản V4.5. Với kiến trúc Docker hóa và CI/CD tự động, hệ thống đã sẵn sàng cho việc mở rộng quy mô mà không cần viết lại từ đầu. Mỗi giai đoạn mở rộng sẽ được xây dựng "chồng lên" nền tảng hiện có, đảm bảo tính ổn định và liên tục trong vận hành.

**Ưu tiên cần làm ngay**: 
1. Kết nối LAN cho Camera (thay WiFi)
2. Tích hợp Telegram Bot cảnh báo
3. Hoàn thiện tab Phân Tích với dữ liệu thực

---
*Tài liệu được cập nhật lần cuối: 01/04/2026 — Sentinel Warden AI Team*
