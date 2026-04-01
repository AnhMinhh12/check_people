# KẾ HOẠCH TRIỂN KHAI HỆ THỐNG AI GIÁM SÁT AN TOÀN LAO ĐỘNG (V4.0)

**Mục tiêu:** Phát hiện sự hiện diện của công nhân trong vùng an toàn (ROI) để đảm bảo tuân thủ quy trình vận hành máy với độ chính xác và ổn định cao nhất.

---

## 1. Hạ tầng & Công nghệ (V4.0 - Industrial Stability)

### Luồng dữ liệu (Data Pipeline)
*   **Camera:** Hỗ trợ Hikvision, Dahua và các dòng IP Camera thông dụng qua RTSP.
*   **Stream:** Tự động tối ưu luồng với cơ chế Multi-threading, đảm bảo Frame Buffer luôn là hình ảnh mới nhất, triệt tiêu hiện tượng trễ hình (Video Lag).
*   **Truyền tải:** Ép sử dụng giao thức TCP thay vì UDP để chống nhiễu và mất gói tin trong môi trường công nghiệp.

### Engine AI & Logic An toàn (Nâng cấp trọng tâm)
*   **Nhận diện:** Sử dụng YOLOv8s (Small) hoặc YOLOv8n (Nano) tùy cấu hình máy, đảm bảo cân bằng giữa tốc độ và độ chính xác.
*   **Multi-point Vertical Scanning (Mới):** 
    *   Thay vì chỉ kiểm tra "điểm chân" duy nhất (dễ bị che hoặc lỗi khi vẽ ROI cao), hệ thống quét **4 điểm quan trọng** trên cơ thể: 100% (Chân), 90%, 75% và 50% (Thân).
    *   **Lợi ích:** Chỉ cần 1 trong 4 điểm này nằm trong ROI, công nhân được coi là AN TOÀN. Điều này giúp hệ thống hoạt động cực kỳ ổn định ngay cả khi công nhân cúi người, bị máy móc che một phần chân.
*   **Chống "Nháy" trạng thái (1s Confirmation Delay):**
    *   Hệ thống áp dụng bộ đệm 1 giây. Trạng thái chỉ chuyển sang "RỜI VỊ TRÍ" khi AI không tìm thấy người trong ROI liên tục 1 giây. Loại bỏ hoàn toàn hiện tượng báo động giả do AI mất dấu khung hình ngắn hạn.
*   **Chống đếm trùng (Advanced NMS):** Tự động lọc bỏ các bounding box chồng lấn (thường do vật cản chia cắt cơ thể thành nhiều phần).

---

## 2. Cấu trúc Source Code Thực tế

1.  **`src/core/camera_stream.py`**: Quản lý kết nối RTSP ổn định.
2.  **`src/core/ai_engine.py`**: Chứa logic YOLOv8 và thuật toán Quét đa điểm (Multi-point).
3.  **`src/core/database.py`**: Quản lý lưu trữ vi phạm vào SQLite.
4.  **`src/services/ai_worker.py`**: Luồng xử lý chính kết nối AI, Camera và SocketIO.
5.  **`app.py`**: Web Server (Flask + SocketIO) cung cấp giao diện Dashboard.

---

## 3. Dashboard Giám sát Thời gian thực

Hệ thống cung cấp giao diện Web mượt mà (5Hz update) qua SocketIO:
*   **LIVE STREAM:** Hình ảnh thực tế từ camera với overlay các khung nhận diện.
*   **STATUS:** Hiển thị trực quan: **AN TOÀN** (Xanh), **RỜI VỊ TRÍ** (Vàng - dưới 5s), **VI PHẠM** (Đỏ - trên 5s).
*   **VIOLATION HISTORY:** Tự động lưu ảnh bằng chứng kèm thời gian vắng mặt chính xác xuống Database.
*   **ROI CONFIG:** Cho phép vẽ và cập nhật vùng an toàn trực tiếp từ giao diện (tự động nạp lại cấu hình mà không cần khởi động lại Server).

---

## 4. Hướng dẫn Triển khai

### 4.1 Chuẩn bị môi trường
1.  **Cài đặt Python:** 3.9+ 
2.  **Môi trường ảo & Thư viện:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```

### 4.2 Chạy ứng dụng
*   Khởi chạy Server: `python app.py`
*   Truy cập Dashboard: `http://localhost:5000`

---

## 5. Yêu cầu Hệ thống Khuyến nghị
*   **Hardware:** Intel Core i5 Gen 10 trở lên, RAM 8GB.
*   **OS:** Windows 10/11 hoặc Linux (Docker supported).
*   **Network:** Băng thông tối thiểu 2MB/s cho mỗi luồng Camera.