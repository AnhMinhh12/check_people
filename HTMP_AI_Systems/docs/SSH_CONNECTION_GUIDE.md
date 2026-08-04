# Hướng dẫn Kết nối Server qua SSH (VS Code & Windows)

Tài liệu này hướng dẫn cách cấu hình và kết nối tới server AI (hoặc bất kỳ server Linux nào) từ máy tính Windows của bạn bằng SSH, giúp tối ưu hóa việc code và quản lý file.

---

## 1. Cấu hình file SSH Config (Khuyên dùng)

Thay vì phải nhớ địa chỉ IP và username, bạn nên cấu hình file `config` để kết nối nhanh bằng tên gợi nhớ.

### Cách thực hiện:
1. Mở file tại đường dẫn: `C:\Users\it07\.ssh\config`
2. Thêm nội dung theo mẫu sau cho server mới:

```ssh
Host Ten-Server-Goi-Nho
    HostName [Địa-chỉ-IP]
    User [Tên-người-dùng]
    IdentityFile "C:\Users\it07\.ssh\id_ed25519"
```

*Ví dụ thực tế:*
```ssh
Host Server-AI-Moi
    HostName 192.168.1.100
    User ubuntu
    IdentityFile "C:\Users\it07\.ssh\id_ed25519"
```

> [!TIP]
> Sau khi lưu file, bạn chỉ cần gõ `ssh Server-AI-Moi` trong Terminal là có thể kết nối ngay.

---

## 2. Tạo SSH Key (Nếu chưa có)

Để kết nối không cần mật khẩu và an toàn hơn, hãy sử dụng SSH Key.

1. Mở PowerShell hoặc CMD.
2. Chạy lệnh:
   ```powershell
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```
3. Nhấn **Enter** liên tục để đồng ý các vị trí mặc định.
4. Key của bạn sẽ được lưu tại `C:\Users\it07\.ssh\id_ed25519`.

---

## 3. Copy SSH Key lên Server

Để server nhận diện máy tính của bạn, bạn cần đưa khóa công khai (`id_ed25519.pub`) lên server.

### Cách làm nhanh trên Windows (PowerShell):
```powershell
cat ~/.ssh/id_ed25519.pub | ssh [User]@[IP-Server] "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```
*(Bạn sẽ cần nhập mật khẩu của server 1 lần duy nhất này)*

---

## 4. Kết nối qua VS Code (Remote - SSH)

Cách này cho phép bạn mở folder trên server và code như thể đang làm việc trên máy cục bộ.

1. Cài đặt Extension: **Remote - SSH** (của Microsoft).
2. Nhấn vào biểu tượng **Remote Explorer** (hình màn hình nhỏ ở thanh bên trái).
3. Tại mục **SSH**, bạn sẽ thấy danh sách các Host đã cấu hình ở bước 1.
4. Chuột phải vào tên server -> Chọn **Connect in Current Window**.
5. Chọn hệ điều hành của server (thường là **Linux**).

---

## 5. Các lỗi thường gặp (Troubleshooting)

| Lỗi | Nguyên nhân | Cách xử lý |
| :--- | :--- | :--- |
| **Connection timed out** | Sai IP hoặc Server đang tắt / chặn Firewall | Kiểm tra ping tới server: `ping [IP]` |
| **Permission denied** | Chưa copy SSH Key hoặc sai Username | Kiểm tra lại bước 3 hoặc kiểm tra file `config` |
| **Host key verification failed** | Server được cài lại hoặc đổi IP | Chạy lệnh: `ssh-keygen -R [IP-Server]` |

---

> [!IMPORTANT]
> Luôn đảm bảo bạn đang kết nối vào mạng nội bộ (hoặc VPN) nếu server nằm trong mạng LAN của công ty.
