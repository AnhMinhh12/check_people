import os
from dotenv import load_dotenv
from src.core.database import DatabaseManager

load_dotenv()
db = DatabaseManager()

# Lấy RTSP mặc định từ ENV
default_url = os.getenv("RTSP_URL", "rtsp://admin:pass@192.168.1.10:554/stream")

# Thêm 3 camera mẫu để test giao diện lưới
cameras = [
    {"name": "Camera Khu Vực A", "url": default_url, "group": "Sản Xuất"},
    {"name": "Camera Khu Vực B", "url": default_url, "group": "Sản Xuất"},
    {"name": "Camera Kho Bãi", "url": default_url, "group": "Logistics"}
]

for cam in cameras:
    cam_id = db.add_camera(cam['name'], cam['url'], cam['group'])
    print(f"Đã thêm {cam['name']} với ID: {cam_id}")

print("\n>>> Seeding hoàn tất. Hãy chạy lại app.py để xem kết quả.")
