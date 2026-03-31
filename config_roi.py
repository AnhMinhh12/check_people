import cv2
import json
import os
import numpy as np
from camera_stream import CameraStreamer

# Cấu hình đường dẫn lưu ROI
CONFIG_FILE = "roi_config.json"
RTSP_URL = "rtsp://admin:Htmp%402019@192.168.103.14:554/Streaming/Channels/102"

# Danh sách chứa các điểm của Polygon
points = []
# Image copy để vẽ overlay
img_display = None
img_original = None
scale_ratio = 1.0

def draw_polygon(event, x, y, flags, param):
    global points, img_display, img_original, scale_ratio
    
    if event == cv2.EVENT_LBUTTONDOWN:
        # Lưu tọa độ đã được scale ngược lại về ảnh gốc
        points.append((int(x / scale_ratio), int(y / scale_ratio)))
        print(f"Đã thêm điểm: {points[-1]}")
    
    elif event == cv2.EVENT_RBUTTONDOWN:
        # Xóa điểm cuối cùng
        if points:
            points.pop()
            print("Đã xóa điểm cuối.")

def main():
    global points, img_display, img_original, scale_ratio
    
    streamer = CameraStreamer(RTSP_URL)
    streamer.start()
    
    print("--- CẤU HÌNH VÙNG AN TOÀN (ROI) ---")
    print("Hướng dẫn:")
    print("1. Chờ camera hiện hình ảnh.")
    print("2. Chuột TRÁI để chọn điểm tạo vùng Polygon.")
    print("3. Chuột PHẢI để xóa điểm vừa chọn.")
    print("4. Nhấn 'S' để LƯU và THOÁT.")
    print("5. Nhấn 'Q' để HỦY và THOÁT.")
    
    cv2.namedWindow("Config ROI")
    cv2.setMouseCallback("Config ROI", draw_polygon)
    
    while True:
        ret, frame, frame_id = streamer.read()
        if not ret or frame is None:
            print("Đang chờ stream camera...")
            cv2.waitKey(1000)
            continue
            
        img_original = frame.copy()
        h, w = img_original.shape[:2]
        
        # Resize để hiển thị vừa màn hình (VD: max width 1280)
        max_display_w = 1280
        scale_ratio = max_display_w / w
        img_display = cv2.resize(img_original, (int(w * scale_ratio), int(h * scale_ratio)))
        
        # Vẽ các điểm và đường nối
        if len(points) > 0:
            # Vẽ các điểm đã chọn (đã scale về tỉ lệ hiển thị)
            scaled_points = np.array([(int(p[0] * scale_ratio), int(p[1] * scale_ratio)) for p in points])
            
            # Vẽ các đường nối
            if len(scaled_points) > 1:
                cv2.polylines(img_display, [scaled_points], isClosed=False, color=(0, 255, 0), thickness=2)
            
            # Vẽ các chấm tại điểm
            for p in scaled_points:
                cv2.circle(img_display, tuple(p), 5, (0, 0, 255), -1)

        cv2.imshow("Config ROI", img_display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'): # Save
            if len(points) < 3:
                print("Lỗi: Vùng ROI phải có ít nhất 3 điểm (Polygon)!")
                continue
            
            config = {
                "roi_polygon": points,
                "original_resolution": [w, h]
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            print(f"Đã lưu cấu hình vào {CONFIG_FILE}")
            break
            
        elif key == ord('q'): # Quit
            print("Đã hủy cấu hình.")
            break

    streamer.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
