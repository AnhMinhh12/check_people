import os
import sys
import io
import requests
import time
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv

# Fix UnicodeEncodeError on Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def sync_ui():
    """
    Script đồng bộ giao diện (UI) từ AI Monitoring Hub.
    Phiên bản 3.0: Hỗ trợ Manifest, Versioning và Safe Backup.
    """
    print("\n" + "="*60)
    print("   AI MONITORING HUB - UI SYNCHRONIZER (VERSION 3.0)")
    print("="*60)
    
    # 1. Load cấu hình
    load_dotenv()
    hub_url = os.getenv("HUB_URL")
    
    if not hub_url:
        print("\n[!] Lỗi: Không tìm thấy HUB_URL trong file .env")
        print("    Vui lòng thêm HUB_URL=http://<ip-cua-hub>:4000 vào .env")
        return

    hub_url = hub_url.rstrip('/')
    cache_buster = int(time.time())
    
    # 2. Lấy Manifest từ Hub
    print(f"\n[*] Đang kết nối tới Hub: {hub_url}...")
    try:
        manifest_url = f"{hub_url}/api/shared/manifest?t={cache_buster}"
        response = requests.get(manifest_url, timeout=10)
        
        if response.status_code == 404:
            # Fallback: Thử tải trực tiếp từ static folder
            manifest_url = f"{hub_url}/static/ui_manifest.json?t={cache_buster}"
            response = requests.get(manifest_url, timeout=10)
            
        if response.status_code != 200:
            print(f"[!] Không thể lấy manifest từ Hub (HTTP {response.status_code})")
            return
        hub_manifest = response.json()
    except Exception as e:
        print(f"[X] Lỗi kết nối tới Hub: {e}")
        return

    hub_version = hub_manifest.get("version", "unknown")
    print(f"[OK] Đã tìm thấy UI Version: {hub_version}")

    # 3. Kiểm tra version local (nếu có)
    local_manifest_path = os.path.join(os.getcwd(), 'ui_manifest.local.json')
    local_version = "none"
    if os.path.exists(local_manifest_path):
        try:
            with open(local_manifest_path, 'r', encoding='utf-8') as f:
                local_manifest = json.load(f)
                local_version = local_manifest.get("version", "none")
        except: pass

    if local_version == hub_version:
        confirm = input(f"\n[?] Phiên bản hiện tại ({local_version}) đã là mới nhất. Bạn có muốn đồng bộ lại không? (y/n): ")
        if confirm.lower() != 'y':
            print("\n[!] Đã hủy đồng bộ.")
            return

    # 4. Bắt đầu đồng bộ
    files_to_sync = hub_manifest.get("files", {})
    success_count = 0
    total_files = len(files_to_sync)
    
    print(f"\n[1/1] Đang đồng bộ {total_files} tệp giao diện...")
    
    # Tạo thư mục backup theo timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(os.getcwd(), 'backups', f'ui_{timestamp}')
    
    for hub_path, local_path in files_to_sync.items():
        # --- PATH MAPPING: Khớp với kiến trúc project hiện tại ---
        if local_path == "app/templates/base.html":
            local_path = "templates/layouts/base.html"
        elif local_path.startswith("app/templates/partials/"):
            local_path = local_path.replace("app/templates/partials/", "templates/partials/")
        elif local_path.startswith("app/templates/"):
            local_path = local_path.replace("app/templates/", "templates/")

        # Phân loại URL (Template API hoặc Static Asset)
        if hub_path.startswith('templates/'):
            template_name = hub_path.replace('templates/', '')
            url = f"{hub_url}/api/shared/templates/{template_name}?t={cache_buster}"
        else:
            url = f"{hub_url}/{hub_path}?t={cache_buster}"
            
        if download_file_with_backup(url, local_path, backup_root):
            # --- POST-PROCESSING: Gỡ bỏ HUB_URL prefix để dùng file local ---
            if local_path.endswith("base.html"):
                try:
                    with open(local_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    new_content = content.replace("{{ config.HUB_URL }}", "")
                    if new_content != content:
                        with open(local_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"  [FIX] Đã gỡ bỏ HUB_URL prefix trong {local_path}")
                except Exception as e:
                    print(f"  [!] Lỗi hậu xử lý {local_path}: {e}")
            
            success_count += 1

    # 5. Lưu manifest local
    if success_count == total_files:
        with open(local_manifest_path, 'w', encoding='utf-8') as f:
            json.dump(hub_manifest, f, indent=4)
        print(f"\n[OK] Đã cập nhật manifest local sang phiên bản {hub_version}")

    print("\n" + "="*60)
    print(f" HOÀN TẤT: Đã đồng bộ {success_count}/{total_files} tệp thành công!")
    print(f" BACKUP: Các tệp cũ đã được lưu tại: {backup_root}")
    print("="*60)
    print("Ghi chú: ")
    print("- Vui lòng khởi động lại Flask server để thấy thay đổi mới nhất.\n")

def download_file_with_backup(url, local_path, backup_root):
    """Tải một file từ URL, có thực hiện backup nếu file đã tồn tại."""
    save_path = os.path.join(os.getcwd(), local_path)
    
    # 1. Thực hiện backup nếu file đã tồn tại
    if os.path.exists(save_path):
        backup_path = os.path.join(backup_root, local_path)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(save_path, backup_path)
    
    # 2. Đảm bảo thư mục đích tồn tại
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 UI-Sync-Tool/3.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Ghi file (xử lý cả text và binary)
            mode = 'wb' if any(ext in local_path for ext in ['.png', '.jpg', '.ico', '.woff']) else 'w'
            encoding = 'utf-8' if mode == 'w' else None
            
            with open(save_path, mode, encoding=encoding) as f:
                if mode == 'w':
                    f.write(response.text)
                else:
                    f.write(response.content)
            print(f"  [OK] {local_path}")
            return True
        else:
            print(f"  [!] Lỗi tải {local_path}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [X] Không thể tải {local_path}: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        sync_ui()
    except KeyboardInterrupt:
        print("\n\n[!] Đã dừng script bởi người dùng.")
        sys.exit(0)
