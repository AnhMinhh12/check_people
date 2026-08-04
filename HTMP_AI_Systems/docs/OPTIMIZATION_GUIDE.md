# Tài liệu Tối ưu hóa Tài nguyên - HTMP AI Systems

Dự án này đã được tối ưu hóa đặc biệt để chạy trên môi trường Server (Windows/Linux) có số lượng nhân CPU lớn (Xeon) và dung lượng RAM cao, nhằm tránh tình trạng nghẽn cổ chai và chiếm dụng tài nguyên vô ích.

## 1. Tối ưu hóa Đa luồng (Thread Management)

Mặc định, các thư viện như PyTorch, OpenCV, và ONNX Runtime sẽ tạo ra số lượng luồng bằng với số nhân CPU cho **mỗi** camera. Trên server có 128 nhân, nếu chạy 10 camera, hệ thống sẽ tạo ra hàng ngàn luồng, gây hiện tượng **Context Switching** cực cao và làm sập ứng dụng.

**Các biện pháp đã áp dụng:**
*   **Khống chế biến môi trường:** Ép cứng `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS` về 1.
*   **Chính sách PASSIVE:** Đặt `OMP_WAIT_POLICY=PASSIVE` để ngăn các luồng C++ chạy vòng lặp bận (Spin-wait) chiếm 100% CPU khi đang rảnh.
*   **OpenCV & PyTorch:** Giới hạn luồng trực tiếp qua code bằng `cv2.setNumThreads(0)` và `torch.set_num_threads(1)`.

## 2. Mô hình AI Dùng chung (Shared Model Pattern)

Thay vì mỗi camera khởi tạo một đối tượng YOLO riêng (tốn hàng trăm MB RAM và tạo thêm luồng riêng), dự án sử dụng cơ chế **Shared Model Instance**:
*   **Singleton Model:** Một model duy nhất được tải lên RAM và dùng chung cho tất cả các AI Workers.
*   **Xử lý tuần tự/Batch:** Các frame từ nhiều camera sẽ được đưa qua cùng một instance model, giúp tiết kiệm tối đa bộ nhớ đệm và băng thông Bus của CPU.

## 3. Tối ưu hóa ONNX Runtime (Monkey Patching)

Chúng tôi đã can thiệp vào quá trình khởi tạo của `onnxruntime` để ép các Session Options:
*   `intra_op_num_threads = 2`: Giới hạn mỗi phép tính toán AI chỉ dùng tối đa 2 luồng.
*   `execution_mode = ORT_SEQUENTIAL`: Chạy các lệnh tính toán theo thứ tự thay vì song song hóa mù quáng gây tranh chấp tài nguyên.
*   **Tắt Spinning:** Vô hiệu hóa tính năng `allow_spinning` của C++ Eigen Threadpool để giảm nhiệt độ CPU khi xử lý.

## 4. Tối ưu hóa Luồng Video (Fine-tuned FFmpeg)

Sử dụng cấu hình FFmpeg tùy chỉnh qua OpenCV để giảm tải việc giải mã (Decoding):
*   `rtsp_transport=tcp`: Chống mất gói tin và giảm nhiễu hình ảnh.
*   `fflags=discardcorrupt`: Bỏ qua các gói tin hỏng thay vì cố gắng sửa (giảm năng lực xử lý).
*   `probesize=32`: Giảm thời gian chờ đợi phân tích stream ban đầu.
*   `threads=1`: Ép mỗi tiến trình đọc camera chỉ dùng duy nhất 1 luồng giải mã.

## 5. Tiết kiệm Băng thông & CPU Dashboard

*   **Selective Streaming:** Chỉ stream ảnh JPEG qua WebSocket cho camera nào đang được người dùng "Focus" (xem chi tiết) hoặc khi bật chế độ Live Grid.
*   **MJPEG Buffer Control:** Tăng kích thước buffer và timeout để tránh việc SocketIO phải kết nối lại liên tục khi gặp frame hình lớn.

## Kết quả đạt được
*   **CPU:** Giảm từ 80-90% xuống còn khoảng 15-30% cho hệ thống 5+ camera trên dòng Xeon Silver/Gold.
*   **RAM:** Tiết kiệm khoảng 400MB - 1GB RAM cho mỗi camera được thêm mới so với cách làm thông thường.
*   **Độ ổn định:** Không còn tình trạng "Invalid frame header" hoặc sập chương trình do cạn kiệt luồng (Thread exhaustion).
