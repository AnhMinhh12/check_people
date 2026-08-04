# BLUEPRINT: HỆ THỐNG QUẢN LÝ DỮ LIỆU TẬP TRUNG (SENTINEL DB)

Tài liệu này hướng dẫn chi tiết cách sử dụng và tái sử dụng mô đun Database của dự án Sentinel AI cho các dự án khác muốn dùng chung cơ sở dữ liệu.

---

## 1. Kiến Trúc Tổng Quan (3-Layer Architecture)

Hệ thống được chia làm 3 lớp tách biệt để đảm bảo khi bạn thay đổi Database (ví dụ từ MySQL sang PostgreSQL) thì code xử lý AI của bạn không bị ảnh hưởng.

1.  **Lớp Kết nối (`connection.py`):** Thiết lập đường ống dẫn dữ liệu.
2.  **Lớp Mô hình (`models.py`):** Định nghĩa hình dáng của dữ liệu (Bảng, Cột).
3.  **Lớp Kho dữ liệu (`repository.py`):** Chứa các hàm nghiệp vụ (Lưu sự kiện, Lấy danh sách camera).

---

## 2. Chi Tiết Các Bảng Dữ Liệu (Schema)

### A. Bảng Camera (`cameras`)
Lưu trữ danh bạ các luồng video đầu vào.
- `id`: Khóa chính (Auto increment).
- `name`: Tên trạm/camera (Dùng để định danh duy nhất trong logic).
- `url`: RTSP URL hoặc Path video file.
- `is_active`: Trạng thái (True: Đang chạy, False: Tạm dừng).

### B. Bảng Vùng Nhận Diện (`zones`)
Lưu tọa độ các khu vực cần giám sát trên khung hình.
- `camera_id`: Liên kết với bảng Camera.
- `zone_name`: Tên vùng (Ví dụ: "Máy dập 01", "Vị trí lắp ráp").
- `roi_polygon`: Lưu dưới dạng **JSON** mảng các tọa độ `[[x1,y1], [x2,y2]...]`.
- `threshold_seconds`: Thời gian ngưỡng để kích hoạt cảnh báo.

### C. Bảng Sự Kiện (`events`)
Lưu nhật ký lịch sử - Đây là bảng dữ liệu lớn nhất.
- `start_time` / `end_time`: Khoảng thời gian diễn ra sự kiện.
- `event_type`: Loại sự kiện (Ví dụ: "Vi phạm", "Hoàn thành bước", "Vắng mặt").
- `snapshot_path`: Đường dẫn đến file ảnh chứng cứ lưu trên ổ đĩa.
- `machines_involved`: Danh sách tên các máy liên quan (Lưu dạng Text).

---

## 3. Hướng Dẫn Tích Hợp Vào Dự Án Mới

Để dùng chung DB này cho dự án khác, hãy làm theo các bước sau:

### Bước 1: Cài đặt thư viện cần thiết
```bash
pip install SQLAlchemy pymysql
```

### Bước 2: Cấu hình biến môi trường
Tạo file `.env` trong dự án mới và trỏ cùng vào địa chỉ MySQL hiện tại:
```env
DATABASE_URL=mysql+pymysql://minhha:Htmp1234@10.0.10.13:3306/ai_system
```

### Bước 3: Copy Module `db`
Copy nguyên thư mục `db/` gồm 3 file vào dự án mới của bạn.

---

## 4. Các Ví Dụ Code Mẫu (Quick Start)

### 4.1. Cách lấy danh sách Camera để xử lý
```python
from db.repository import CameraRepository

repo = CameraRepository()
cameras = repo.get_all(active_only=True)

for cam in cameras:
    print(f"Đang khởi động AI cho: {cam['name']} - URL: {cam['url']}")
```

### 4.2. Cách lưu một sự kiện vi phạm mới
```python
from db.repository import EventRepository
from datetime import datetime

event_repo = EventRepository()

# Giả sử phát hiện vi phạm tại Camera ID 1
event_repo.save_event(
    camera_id=1,
    zone_id=5,
    event_type="Xâm nhập vùng cấm",
    snapshot_path="/data/images/violation_001.jpg",
    machines_involved="Máy hàn số 2"
)
```

### 4.3. Cách lấy dữ liệu thống kê (Cho Dashboard mới)
```python
from db.repository import EventRepository

event_repo = EventRepository()
# Lấy 10 sự kiện gần nhất
history = event_repo.get_history(limit=10)
```

---

## 5. Lưu Ý Quan Trọng Khi Dùng Chung DB

1.  **Tính Nhất Quán:** Nếu dự án A sửa đổi cấu trúc bảng trong `models.py` (ví dụ thêm cột mới), dự án B cũng phải cập nhật file `models.py` tương ứng để tránh lỗi "Unknown column".
2.  **Concurrency (Đồng thời):** MySQL xử lý đa luồng rất tốt, nhưng hãy đảm bảo bạn sử dụng `with get_session()` như trong code mẫu để đảm bảo session được đóng ngay sau khi dùng, tránh treo kết nối (Connection Leak).
3.  **Tọa độ ROI:** Tọa độ trong bảng `zones` được tính theo tỷ lệ hoặc pixel tùy cấu hình. Dự án mới cần thống nhất cách đọc tọa độ này với dự án cũ để vẽ khung hình cho khớp.

---
*Tài liệu này được soạn thảo để phục vụ việc mở rộng hệ thống Sentinel AI.*
