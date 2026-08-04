# 🖥️ Hướng dẫn Giám sát Tài nguyên Server (Cẩm nang Warden AI)

Tài liệu này giải thích chi tiết các thông số kỹ thuật khi bạn kiểm tra server bằng lệnh `htop` hoặc `ps aux`.

---

## 1. Giải mã màn hình `htop` (Trực quan nhất)

### A. Khu vực biểu đồ (Phía trên)
*   **Số 0 - 15 (CPU Cores):** Mỗi số đại diện cho 1 nhân CPU.
    *   **Màu Xanh lá:** Sức mạnh đang dùng cho ứng dụng của bạn (AI, Python). **(Tốt nhất nếu chiếm đa số)**.
    *   **Màu Đỏ:** Sức mạnh đang dùng cho hệ thống (Kernel). Nếu đỏ quá nhiều (>50%) là server đang gặp lỗi hệ thống.
    *   **Màu Xanh dương:** Các tác vụ ưu tiên thấp.
*   **Mem (RAM):** 
    *   **Màu Xanh lá:** RAM thực tế đang dùng.
    *   **Màu Xanh dương/Vàng:** Bộ nhớ đệm (Cache/Buffer). Linux tự dùng RAM dư để làm đệm cho nhanh, đừng lo lắng nếu thấy dải này hơi dài.
*   **Swp (Swap):** Bộ nhớ ảo trên ổ cứng. **Luôn nên ở mức 0 hoặc rất thấp.** Nếu Swp nhảy cao, server sẽ cực kỳ lag.
*   **Load Average:** Chỉ số tải trung bình trong 1, 5 và 15 phút. 
    *   *Quy tắc:* Nếu số này nhỏ hơn số nhân CPU (16) là server vẫn đang rảnh.

### B. Các cột thông số (Phía dưới)
| Cột | Ý nghĩa | Ghi chú |
|:---|:---|:---|
| **PID** | ID tiến trình | Dùng để tắt (kill) khi cần. |
| **USER** | Chủ sở hữu | Ai đang chạy lệnh này. |
| **RES** | RAM thực tế | Con số chính xác phần mềm đang ăn bao nhiêu RAM (Ví dụ: 1.2G). |
| **CPU%** | % CPU | Mức độ chiếm dụng của **1 nhân** CPU. |
| **MEM%** | % RAM | Tỷ lệ % RAM chiếm dụng trên tổng số RAM server có. |
| **Command** | Lệnh chạy | Tên phần mềm (ví dụ: `python3.11 -m app.main`). |

---

## 2. Giải mã lệnh `ps aux` (Dạng liệt kê)

Dùng khi bạn muốn lấy nhanh mã số PID để tắt phần mềm.

*   **USER:** Người dùng khởi chạy.
*   **PID:** **Mã số quan trọng nhất** (dùng lệnh `kill PID` để tắt).
*   **%CPU / %MEM:** Tương tự `htop`.
*   **STAT (Status):** 
    *   `R`: Đang chạy (Running).
    *   `S`: Đang nghỉ/đợi (Sleeping).
    *   `Z`: Tiến trình "thây ma" (Zombie - đã chết nhưng chưa biến mất).

---

## 3. Các phím tắt "Quyền năng" trong `htop`

*   **`F3`**: Tìm kiếm tên phần mềm.
*   **`F4`**: **Bộ lọc (Filter)** - Gõ `python` để chỉ xem đúng AI của mình. (Khuyên dùng).
*   **`F5`**: Xem theo dạng cây (biết luồng nào sinh ra luồng nào).
*   **`F6`**: Sắp xếp theo cột (CPU, RAM...).
*   **`F9`**: Tắt ngay tiến trình đang chọn (Kill).
*   **`F10`**: Thoát khỏi htop.

---

## 4. Dấu hiệu nhận biết Server "Khỏe" hay "Yếu"

| Trạng thái | Dấu hiệu | Hành động |
|:---|:---|:---|
| **Rất Khỏe** | CPU < 50%, RAM < 70%, Swp = 0. | Cứ yên tâm cho chạy. |
| **Hơi Đuối** | Một vài nhân CPU đỏ rực 100% liên tục. | Kiểm tra lại số lượng camera. |
| **Nguy kịch** | RAM đầy, Swp nhảy cao, Load Average > 16. | Tắt bớt các ứng dụng không cần thiết hoặc nâng cấp RAM/CPU. |

---
**Mẹo:** Bạn có thể gõ `bash status.sh` (file tôi đã tạo) để xem bản tóm tắt siêu rút gọn của các thông số này!
