# KẾ HOẠCH TRIỂN KHAI HỆ THỐNG AI GIÁM SÁT AN TOÀN LAO ĐỘNG

**Mục tiêu:** Phát hiện sự hiện diện của công nhân trong vùng an toàn (ROI) để đảm bảo tuân thủ quy trình vận hành máy.
**Core Logic:** Sử dụng AI YOLOv8n kết hợp với logic **"Foot-Point Detection"** để xác định vị trí đứng thực tế của công nhân, giúp loại bỏ hoàn toàn các báo động giả do người đi ngang qua ở tiền cảnh.

---

## 1. Hạ tầng & Công nghệ (V3.0 - Robustness Edition)

### Luồng dữ liệu (Data Pipeline)
*   **Camera:** Hikvision IP Camera (Dòng 2K/4K).
*   **Stream:** Luồng phụ 102 (H.264/H.265) để đảm bảo băng thông và giảm độ trễ xử lý.
*   **Module Streamer:** Đa luồng (Multi-threading) với cơ chế tự động kết nối lại (Auto-reconnect) và gắn mã định danh khung hình (Frame ID) để phát hiện lag mạng.

### Engine AI & Logic An toàn
*   **Nhận diện:** YOLOv8n (Model Nano tối ưu tốc độ) với ngưỡng tin tưởng `conf=0.2`.
*   **Xử lý tọa độ (Foot-Point Logic):** 
    *   Hệ thống chỉ kiểm tra vị trí đôi chân (Điểm chính giữa mép dưới Bounding Box).
    *   Giúp phân biệt người đang đứng trong vùng (SAFE) và người vô tình đi ngang qua phía trước camera (WARNING).
*   **Chống che khuất (Occlusion):** Sử dụng **Mask-based Intersection** trên mặt sàn. Khi chân bị bảng hiệu che, điểm mép dưới của khung người vẫn nằm trong vùng sàn nhà đã vẽ $\rightarrow$ Duy trì trạng thái SAFE.
*   **Chống báo động giả do Mạng Lag (Anti-Lag Timer):** 
    *   Sử dụng cơ chế cộng dồn thời gian thực (`time_delta`) giữa các khung hình mới. 
    *   **Nếu mạng đứng hình (Freezing):** Bộ đếm 5 giây sẽ **tự động tạm dừng**, không tính oan thời gian vắng mặt cho công nhân.

---

## 2. Các thành phần chính của source code

1.  **`camera_stream.py`**: Quản lý kết nối RTSP, đọc frame background.
2.  **`config_roi.py`**: Công cụ vẽ vùng đa giác ROI và lưu cấu hình JSON.
3.  **`ai_engine.py`**: Trái tim của hệ thống – chạy YOLO và kiểm tra điểm chân vào Mask.
4.  **`test.py`**: File chạy chính tích hợp Dashboard đo lường hiệu năng thời gian thực.

---

## 3. Hệ thống Giám sát Hiệu năng (Telemetry Dashboard)

Hệ thống in Log mỗi 5 giây để quản lý có thể "khám bệnh" hạ tầng mạng:
*   **NETWORK FPS:** Tốc độ khung hình thực tế từ Camera gửi về.
*   **AI INFERENCE:** Thời gian AI xử lý (ms) – giúp đánh giá tải trọng CPU/GPU.
*   **MISSING ACCUMULATED:** Thời gian vắng mặt tích lũy (Chỉ đếm khi có hình mới).

---

## 4. Trạng thái Hiển thị (Visual UI)
*   **XANH (SAFE):** Có ít nhất 1 điểm chân của công nhân nằm trong vùng ROI.
*   **ĐỎ (WARNING):** Không có điểm chân nào trong vùng ROI liên tục quá 5 giây.
*   **CHẤM TRÒN:** Hiển thị trực tiếp vị trí "Chân" mà AI đang bắt để người vận hành dễ dàng điều chỉnh vị trí đứng.

---

### Kết quả đạt được:
- [x] Khắc phục lỗi báo ảo khi chân bị che khuất.
- [x] Khắc phục lỗi báo ảo khi mạng lag/đứng hình.
- [x] Loại bỏ báo động nhầm do người đi ngang qua tiền cảnh.
- [x] Hiển thị dashboard chi tiết để theo dõi hạ tầng.

---

## 5. Hướng dẫn Triển khai (Deployment Guide)

### 5.1 Chuẩn bị môi trường
1.  **Cài đặt Python:** Tải và cài đặt Python 3.9 trở lên (đảm bảo tích hợp vào PATH).
2.  **Tạo môi trường ảo (venv):**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  **Cài đặt thư viện:**
    ```bash
    pip install -r requirements.txt
    ```

### 5.2 Cấu hình Hệ thống
Hệ thống sử dụng file `.env` để quản lý các thông số môi trường. Bạn có thể chỉnh sửa các thông số sau trong file `.env`:
*   `RTSP_URL`: Đường dẫn luồng camera (Hikvision/Dahua/...).
*   `ALARM_DELAY_SECONDS`: Thời gian vắng mặt cho phép (mặc định 5s).
*   `FLASK_PORT`: Cổng chạy website (mặc định 5000).

### 5.3 Chạy ứng dụng
Hệ thống cung cấp hai cách chạy:
1.  **Chế độ Phát triển (Development):**
    ```bash
    python app.py
    ```
2.  **Chế độ Sản xuất (Production - Khuyên dùng):** Sử dụng Waitress để đảm bảo tính ổn định 24/7 trên Windows.
    ```bash
    python run_server.py
    ```

### 5.4 Yêu cầu Phần cứng Khuyến nghị
*   **CPU:** Intel Core i5 Gen 10th hoặc tương đương.
*   **RAM:** 8GB DDR4.
*   **GPU:** (Tùy chọn) NVIDIA GTX 1650 trở lên để tối ưu tốc độ AI (cần cài đặt thêm CUDA/cuDNN).
*   **Mạng:** Kết nối LAN nội bộ ổn định cho Camera RTSP.