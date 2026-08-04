import os
import sys
import socket
from datetime import datetime

# Add HTMP_AI_Systems to python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config import settings
from db.repository import CameraRepository, ZoneRepository

def test_rtsp_port(url):
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        netloc = parsed.netloc
        if "@" in netloc:
            netloc = netloc.split("@")[-1]
        if ":" in netloc:
            host, port = netloc.split(":")
            port = int(port)
        else:
            host = netloc
            port = 554  # Default RTSP port
        
        print(f"[*] Testing TCP connection to RTSP host {host}:{port}...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3.0)
        s.connect((host, port))
        s.close()
        return True, f"Successfully connected to {host}:{port}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("        HTMP AI SYSTEM - DIAGNOSTIC TOOL FOR CAMERA 15")
    print("=" * 60)
    
    # 1. Database Connection and Camera Info
    print("\n[1] Checking Database Configuration...")
    try:
        cam_repo = CameraRepository()
        zone_repo = ZoneRepository()
        
        cam = cam_repo.get_by_id(15)
        if not cam:
            print("[!] CAMERA WITH ID 15 NOT FOUND IN DATABASE!")
            all_cams = cam_repo.get_all(active_only=False)
            print("Available cameras in DB:")
            for c in all_cams:
                print(f" - ID {c['id']}: {c['name']} ({c['url']})")
        else:
            print(f"[OK] Camera Found: ID={cam['id']}, Name='{cam['name']}', Active={cam['active']}")
            print(f"     RTSP URL: {cam['url']}")
            
            # Check Zones
            zones = zone_repo.get_by_camera(15)
            if not zones:
                print("[!] WARNING: No active zones (ROI) found in database for Camera 15!")
            else:
                print(f"[OK] Found {len(zones)} active zones for Camera 15 in database:")
                for z in zones:
                    print(f"     - Zone ID {z['id']}: '{z['name']}' (Type: {z['type']})")
                    print(f"       ROI Points: {z['roi']}")
            
            # Test RTSP connectivity
            ok, msg = test_rtsp_port(cam['url'])
            if ok:
                print(f"[OK] RTSP Stream Port Test: {msg}")
            else:
                print(f"[!] RTSP Stream Port Test FAILED: {msg}")
                print("     Please check network routing, IP address, or camera credentials.")
    except Exception as e:
        print(f"[!] Error checking database/network: {e}")

    # 2. Check Local logs
    print("\n[2] Checking Camera 15 Log Files...")
    logs_dir = settings.LOGS_DIR
    if not os.path.exists(logs_dir):
        print(f"[!] Logs directory '{logs_dir}' does not exist.")
        return
        
    log_files = [f for f in os.listdir(logs_dir) if f.startswith("camera_15") and f.endswith(".log")]
    if not log_files:
        print("[!] No log files starting with 'camera_15' found.")
        return
        
    print(f"Found {len(log_files)} log file(s) for Camera 15:")
    for f in log_files:
        path = os.path.join(logs_dir, f)
        mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
        size_kb = os.path.getsize(path) / 1024.0
        print(f" - {f} (Last Modified: {mtime}, Size: {size_kb:.2f} KB)")
        
    # Read the latest log file
    latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(logs_dir, f)))
    latest_log_path = os.path.join(logs_dir, latest_log)
    print(f"\n--- Reading last 50 lines of '{latest_log}' ---")
    try:
        with open(latest_log_path, 'r', encoding='utf-8', errors='ignore') as lf:
            lines = lf.readlines()
            for line in lines[-50:]:
                print(line.strip())
                
        # Search for errors/warnings in last 1000 lines
        print("\n--- Searching for Warnings/Errors/Exceptions in last 1000 lines ---")
        warnings_errors = []
        for line in lines[-1000:]:
            lower_line = line.lower()
            if "warning" in lower_line or "error" in lower_line or "exception" in lower_line or "failed" in lower_line or "không tìm thấy" in lower_line:
                warnings_errors.append(line.strip())
                
        if warnings_errors:
            print(f"Found {len(warnings_errors)} warning/error lines:")
            for line in warnings_errors[-20:]:
                print(f" [!] {line}")
        else:
            print("No warnings or errors found in the last 1000 lines.")
    except Exception as e:
        print(f"[!] Error reading log file: {e}")

if __name__ == "__main__":
    main()
