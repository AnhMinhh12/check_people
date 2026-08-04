# 📋 KẾ HOẠCH MUA SẮM GPU CHO HỆ THỐNG SENTINEL WARDEN AI

Dựa trên yêu cầu xây dựng hệ thống **lập trình và nhận diện AI qua Camera**, dưới đây là bản kế hoạch và phân tích chi tiết để bạn lựa chọn GPU cũng như thiết lập cấu hình thiết bị phù hợp nhất.

## 0. MỤC ĐÍCH CHÍNH & QUY TẮC CỐT LÕI (Sống Còn)

Mục đích chủ đạo của dự án là **Lập trình Camera AI** (đọc, bóc tách và phân tích các luồng Video RTSP/IP liên tục theo thời gian thực). Các thuật toán Deep Learning rất nhạy cảm với phần cứng, do đó BỘ PHẬN MUA SẮM VÀ IT CẦN TUÂN THỦ NGHIÊM NGẶT 2 quy định sau:

> [!IMPORTANT]
> **1. Quy tắc về Hãng GPU: CHỈ MUA NVIDIA**
> Mọi bộ mã nguồn (Source code) lập trình AI của dự án (dựa trên PyTorch, ONNX, YOLO) đều gọi trực tiếp vào tập lệnh cốt lõi **CUDA** và **cuDNN** của phần cứng NVIDIA để xử lý ma trận và khởi chạy thuật toán.
> Nếu chọn mua card của hãng AMD (Radeon) hoặc Intel (Arc), toàn bộ hệ thống code sẽ hoàn toàn tê liệt (không thể compile/biên dịch khởi chạy) hoặc buộc phải chạy bằng CPU với tốc độ giật lag không thể ứng dụng.

> [!WARNING]
> **2. Cấu hình phần cứng đi kèm tối thiểu (Minimum Requirements)**
> Kỹ sư AI sẽ không thể lập trình trơn tru nếu GPU xịn nhưng các nền tảng linh kiện khác bị nghẽn (Bottleneck):
> - **CPU (Vi xử lý):** Tối thiểu từ Intel Core i5/i7 (Thế hệ 12 trở lên) hoặc AMD Ryzen 5/7 đời mới. Nhiệm vụ của CPU rất khắc nghiệt: nó phải gánh vác khâu giải nén luồng H264/H265 từ camera trước khi đút khung hình vào cho GPU nhận diện. CPU yếu sẽ gây đứt đoạn kết nối và giật hình liên tục.
> - **RAM Hệ thống:** Tuyệt đối không dưới **32GB DDR4/DDR5**. Cần không gian RAM khổng lồ để lưu trữ các mảng Queue (luồng đợi) video song song.
> - **Nguồn điện (PSU):** Phải đảm bảo chuẩn 80 Plus cấp điện liên tục không trồi sụt. **Tối thiểu 750W** cho RTX 4060Ti/L4 và **1000W** nếu dùng quái vật hạng nặng (RTX 4090).

---

## 1. LOẠI GPU NÀO PHÙ HỢP VỚI PHÒNG SERVER 24/7?

Do công ty bạn đã trang bị **phòng Server tiêu chuẩn với điều hòa lạnh 24/7**, các rào cản về quá nhiệt (overheating) đã được loại bỏ hoàn toàn. Lúc này, bạn có thể tự tin triển khai các **dòng máy chủ chuyên nghiệp** đúng chuẩn thay vì chỉ chọn các dòng Workstation giá rẻ để tự tản nhiệt.

**1. Dòng Card Máy Chủ (Data Center / Enterprise như NVIDIA T4, L4, A10, A100):**
- **Sự lựa chọn hoàn hảo nhất:** Đây là dòng card thiết kế chuẩn thụ động (passive-cooling, hoàn toàn không có quạt). Nó bắt buộc phải nằm trong tủ rack của phòng lạnh thổi luồng gió áp suất cao qua bộ nhôm tản nhiệt.
- **Ưu điểm Tuyệt Đối:** Thiết kế chuyên dụng để bật 24/7/365 không cần nghỉ lễ. Khả năng giải mã luồng video đồng thời (NVDEC) cực khủng, tối ưu cho dự án xử lý rất nhiều nguồn cam cùng lúc trên một hệ thống. 
- **Nhược điểm:** Giá thành đầu tư thiết bị vật lý rất cao.

**2. Dòng GeForce RTX (Workstation - Lợi dụng môi trường lạnh):**
- **Tại sao vẫn dùng được:** Các dòng card RTX vốn bị chê là nóng nếu đặt ở văn phòng thông thường. Nhưng khi đưa hệ thống RTX 3090, 4090 vào phòng server 24/7, yếu điểm nhiệt độ bị triệt tiêu 100%. 
- **Ưu điểm:** Đem lại một cỗ máy chạy AI có tỷ lệ P/P (hiệu năng/giá thành) vô cùng xuất sắc nhờ chi phí phần cứng rẻ hơn Data Center rất nhiều mà dung lượng VRAM vẫn khổng lồ.

---

## 2. TIÊU CHÍ QUAN TRỌNG NHẤT: VRAM (Bộ nhớ đồ họa)

> [!TIP]
> Trong mảng AI xử lý hàng chục luồng camera, **Dung lượng VRAM quan trọng hơn Tốc độ chip GPU**.
> Khi nạp 1 Camera + Mô hình YOLOv8, hệ thống tốn một lượng VRAM cố định. Nếu nghẽn Chip xử lý, số khung hình (FPS) chỉ bị giảm bớt (hình hơi giật). Nhưng nếu cạn 100% VRAM, toàn bộ ứng dụng AI sẽ văng lập tức (Lỗi Out of Memory). Do đó, VRAM càng lớn càng nhồi được nhiều Camera.

---

## 3. CÁC PHƯƠNG ÁN ĐỀ XUẤT MUA SẮM (Theo Không Gian Phòng Server)

### 🥉 LỰA CHỌN 1: GIẢI PHÁP KINH TẾ (Dành Cho Rack Workstation)
**NVIDIA GeForce RTX 4060 Ti (Bản 16GB VRAM) hoặc RTX 4090 (24GB)**

* **Phân loại:** Dòng tiêu dùng / Workstation.
* **Giá dự kiến:** ~13.000.000đ (4060 Ti) đến ~55.000.000đ (4090).
* **Sức chịu đựng dự kiến:** 4060 Ti kéo được 35 - 45 Camera. Còn 4090 dư sức gánh 50-75+ Camera tốc độ cao.
* **Lý do nên mua:** Nhờ có phòng server lạnh 24/7, những chiếc card này vốn dễ bị quá nhiệt nay lại thành "hổ mọc thêm cánh". GPU sẽ duy trì ở nhiệt độ cực kỳ mát, tăng tuổi thọ linh kiện lên tối đa, trong khi tiết kiệm đến 70% ngân sách so với đầu tư máy chủ Server chính thống.

### 🥈 LỰA CHỌN 2: CHUẨN MỰC CHUYÊN DỤNG DOANH NGHIỆP (Data Center)
**NVIDIA L4 (Bản 24GB VRAM) - Nữ hoàng AI thế hệ mới**

* **Phân loại:** Card máy chủ Server chuyên dụng (Low-profile, passive cooling).
* **Giá dự kiến:** ~50.000.000đ - 65.000.000đ.
* **Sức chịu đựng dự kiến:** Tối ưu hóa cực sâu cho phân tích video băng thông lớn, dễ dàng xử lý đồng thời từ 60 - 80+ Camera song song.
* **Lý do nên mua:** 
    - NVIDIA L4 được sinh ra để thay thế "huyền thoại" T4 cũ. Nó sở hữu kiến trúc Ada Lovelace mới nhất.
    - Lõi giải mã Video NVDEC của L4 gấp nhiều lần mức độ giải mã của một chiếc RTX thông thường, giúp cho CPU hoàn toàn thảnh thơi.
    - Lắp vừa khít cực đẹp và chuyên nghiệp vào các khay Server chạng 1U, 2U tiêu chuẩn mà công ty bạn đang trang bị trong phòng lạnh.

### 🥇 LỰA CHỌN 3: QUÁI VẬT TỔNG ĐÀI CỠ LỚN (Data Center Cao Cấp)
**NVIDIA A30 (24GB) hoặc NVIDIA A100 (40GB/80GB)**

* **Phân loại:** Trái tim của siêu máy chủ cấp độ quốc gia/tập đoàn lớn.
* **Giá dự kiến:** ~100.000.000đ đến vài trăm triệu đồng / card.
* **Sức chịu đựng dự kiến:** Xử lý hàng trăm Camera độ phân giải cao hoặc chạy song song cùng lúc hàng trăng Pipeline AI (Nhận diện vật thể + Khuôn mặt + Biển số + Hành vi) xếp chồng lên nhau.
* **Lý do nên mua:** Khi và chỉ khi công ty bạn trực tiếp đóng vai trò như một Central Hub làm dịch vụ AI tập trung cho nhiều nhà xưởng / công ty con thành viên khác đổ dữ liệu về.

---

## 4. TỔNG KẾT & QUYẾT ĐỊNH

> [!NOTE]
> **Khuyến nghị Lựa chọn Chốt Hạ (Với Hệ Sinh Thái Tủ Rack Lạnh):**
> 1. Trọng tâm là **Lợi nhuận - Tiết kiệm chi phí đầu tư:** Mua bộ PC Server chạy **RTX 4060 Ti 16GB** (hoặc RTX 4090) bỏ thẳng vào phòng lạnh. Hệ thống vẫn rất thọ và giá thành rẻ mạt so với dòng chuyên dụng.
> 2. Trọng tâm là **Đồng bộ hóa hạ tầng Data Center chuẩn chỉ:** Yêu cầu đối tác cung cấp thiết bị máy chủ Rack gắn card **NVIDIA L4 (24GB)**. Sức mạnh giải mã vi luồng dòng chuyên nghiệp này sẽ không bao giờ làm các sếp IT thất vọng.
