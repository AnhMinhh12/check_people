# Hướng Dẫn Di Trú Hệ Thống Lên GPU (NVIDIA GTX 1660)

Hệ thống HTMP Sentinel Warden AI được kiến trúc sẵn khả năng tự động nhận diện phần cứng. Dưới đây là hướng dẫn chi tiết để tối ưu hóa hệ thống cho **GPU GTX 1660** và phiên bản **Python 3.11.9**.

> [!CAUTION]
> **LƯU Ý VỀ PYTHON:** Server của bạn có Python 3.10 là bản mặc định của hệ thống. **TUYỆT ĐỐI KHÔNG GỠ BẢN 3.10** vì sẽ làm hỏng hệ điều hành. Chúng ta sẽ cài đặt thư viện vào bản **Python 3.11.9** đã được cài thêm.

---

## BƯỚC 1: Cấu Hình Python 3.11

Mọi lệnh cài đặt phải sử dụng tiền tố chính xác của Python 3.11:
-   **Windows:** Sử dụng `python` (Vì máy bạn đã cấu hình `python` trỏ đến 3.11.9).
-   **Linux/Server:** Sử dụng `python3.11`.

---

## BƯỚC 2: Gỡ Bỏ Thư Viện Chạy CPU (Cũ)

Mở Terminal và chạy lệnh sau (Ví dụ dùng `python` cho Windows):

```bash
python -m pip uninstall onnxruntime torch torchvision -y
```

---

## BƯỚC 3: Cài Đặt Thư Viện Xử Lý GPU (NVIDIA CUDA)

1. **Cài ONNX Runtime GPU:**
   ```bash
   python -m pip install onnxruntime-gpu==1.17.0
   ```

2. **Cài PyTorch bản dành cho GPU CUDA (Phiên bản tối ưu cho CUDA 11.8):**
   ```bash
   python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

---

## BƯỚC 4: Tối Ưu Cho GPU GTX 1660 (6GB VRAM)

> [!IMPORTANT]
> **Lưu ý về sức mạnh phần cứng:** 
> Card **GTX 1660** có dung lượng bộ nhớ đồ họa là **6GB**. 
> - **Số lượng Camera khuyến nghị:** 10 - 15 Camera song song.
> - **Mô hình AI:** Khuyến nghị duy trì sử dụng `yolov8n.onnx` (Nano). 
> - **Cảnh báo:** Nếu nâng lên model `yolov8s` hoặc `yolov8m`, lượng VRAM tiêu thụ sẽ tăng gấp đôi/gấp ba, dễ dẫn đến lỗi văng chương trình (Out of Memory) khi chạy nhiều camera.

**Thay đổi cấu hình trong `.env`:**
```env
# Giữ nguyên bản Nano để chạy được nhiều cam trên 6GB VRAM
MODEL_PATH=models/yolov8n.onnx
```

---

## 🤖 Khởi Chạy Và Kiểm Tra

Để khởi chạy hệ thống, hãy dùng lệnh (Windows):

```bash
python -m app.main
```

Hệ thống sẽ tự động tự kiểm tra phần cứng. Nếu nó tìm thấy GPU, nó sẽ tự chuyển sang chế độ `cuda`.
Chúc hệ thống của bạn bứt tốc thành công!
