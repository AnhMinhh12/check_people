"""
tools/sync_db.py — Công cụ cưỡng bức đồng bộ Camera và Vùng ROI từ file vào Database.
Sử dụng khi chuyển server mới hoặc Database bị lệch thông tin.
"""
import os
import sys
import json

import io

# Fix UnicodeEncodeError on Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Thêm đường dẫn gốc dự án
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config import settings
from db.repository import CameraRepository, ZoneRepository

def sync_all():
    cam_repo = CameraRepository()
    zone_repo = ZoneRepository()

    print(">>> Đang kiểm tra cấu hình .env...")
    camera_configs = settings.get_camera_configs()
    print(f"Tìm thấy {len(camera_configs)} camera trong file .env.")

    # 1. Đồng bộ Camera
    for name, url in camera_configs:
        print(f" - Đang đồng bộ Camera: {name} ({url})")
        cam_repo.sync(name, url)
    
    if camera_configs:
        cam_repo.delete_orphaned(camera_configs)
    
    # 2. Lấy danh sách camera sau khi đồng bộ
    db_cameras = cam_repo.get_all(active_only=False)
    
    # 3. Đồng bộ Vùng ROI từ JSON vào DB
    print("\n>>> Đang đồng bộ vùng ROI từ thư mục data/...")
    for cam in db_cameras:
        cam_id = cam['id']
        json_path = os.path.join(PROJECT_ROOT, f"../data/roi_config_{cam_id}.json")
        
        if os.path.exists(json_path):
            print(f" - Tìm thấy cấu hình JSON cho Camera ID {cam_id}. Đang đẩy vào DB...")
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    zones_data = config.get('roi_zones', [])
                    if zones_data:
                        zone_repo.update_camera_zones(cam_id, zones_data)
                        print(f"   [OK] Đã sync {len(zones_data)} vùng.")
                    else:
                        print("   [!] File JSON trống hoặc không có vùng.")
            except Exception as e:
                print(f"   [!] Lỗi đọc file JSON ID {cam_id}: {e}")
        else:
            print(f" - Không tìm thấy file JSON: roi_config_{cam_id}.json (Bỏ qua)")

    print("\n✅ HOÀN TẤT ĐỒNG BỘ! Hãy restart lại hệ thống và kiểm tra Dashboard Report.")

if __name__ == "__main__":
    sync_all()
