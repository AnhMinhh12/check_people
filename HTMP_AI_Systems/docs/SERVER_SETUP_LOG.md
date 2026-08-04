# 📊 Nhật Ký Thiết Lập Server (Server Setup Log)

Tài liệu này đánh dấu và ghi chú lại tất cả các phương án cấu hình tùy biến, môi trường, và các công cụ bổ trợ đã được triển khai "thực chiến" trên Server vật lý của dự án.

## 1. Thông Tin Phần Cứng & Môi Trường (Cấu hình GTX 1660)
- **Thiết bị GPU:** NVIDIA GeForce GTX 1660 (TU116) - Dung lượng 6GB VRAM.
- **Quy định dùng Python:** Bắt buộc sử dụng phiên bản `Python 3.11` (Bản cài đặt song song để không ghi đè lên Python 3.10 mặc định bảo vệ OS). Toàn bộ thao tác chạy ứng dụng và cài thư viện phải chỉ định rõ bằng lệnh `python3.11` và `pip3.11`.
- **Mô hình AI quy chuẩn:** Khóa cứng phiên bản `yolov8n.onnx` (Nano). Do giới hạn VRAM chỉ 6GB, việc dùng bản Nano sẽ giúp kéo được số lượng camera song song (10-15 cam) mà không dính lỗi Out of Memory.

## 2. Tối Ưu File Khởi Chạy Tự Động (`run.sh`)
Nhằm bịt các lỗ hổng phát sinh khi chạy trên hệ điều hành Linux cục bộ, file `run.sh` đã được thiết lập các cơ chế sau:
- **Tích hợp Shared Library NVIDIA (LD_LIBRARY_PATH):** Tự động truy vết và nối đường dẫn tập lệnh thư viện lõi của CUDA nằm trong thư mục `site-packages/nvidia` của `python3.11` vào hệ thống. Giải quyết triệt để bệnh "không tìm thấy cuDNN" khi trỏ sang GPU mới.
- **Chế độ Offline Vĩnh Viễn:** Kích hoạt các cờ `YOLO_OFFLINE=True` và `ULTRALYTICS_OFFLINE=True`. Tác dụng là ngăn chặn Ultralytics tự động chui ra ngoài Internet ping tải model mới hoặc tải updates, đảm bảo hệ thống duy trì được tính độc lập ổn định trong mạng nội bộ.
- **Khởi chạy chuẩn xác định:** Kết thúc file luôn tự động gọi nhánh `python3.11 -m app.main`.

## 3. Giám Sát Toàn Diện Với Netdata
Để kiểm soát hiệu năng liên tục 24/7, hệ thống **Netdata** Monitor đã được cài gắn liền vào OS của máy chủ:
- Phân tích và biểu đồ hóa tức thời áp lực lên % CPU, % RAM và băng thông đường truyền RTSP tải xuống cực kì chi tiết.
- Giám sát toàn vẹn Card Màn Hình: Có các module đo đạc trực tiếp vào VRAM của GTX 1660, nhiệt độ hoạt động và năng lượng điện tiêu thụ.
- Cho phép bộ phận IT/Admin theo dõi và đánh giá được "Bao nhiêu luồng camera là kịch kim giới hạn của card 6GB" nhằm đưa ra phương án phân tải an toàn.
- **Trạng thái hiện tại:** Đã chủ động tắt và vô hiệu hóa (Disabled) để tiết kiệm tài nguyên hệ thống. Chỉ bật lại khi cần kiểm tra chuyên sâu hoặc bảo trì định kỳ.
