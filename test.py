import cv2
import json
import os
import time
import logging
import numpy as np
from camera_stream import CameraStreamer
from ai_engine import AIEngine

# Cấu hình log chuyên sâu
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("SafetyMonitor")

# Cấu hình
RTSP_URL = "rtsp://admin:Htmp%402019@192.168.103.14:554/Streaming/Channels/102"
CONFIG_FILE = "roi_config.json"

def main():
    streamer = CameraStreamer(RTSP_URL)
    streamer.start()
    
    engine = AIEngine(model_path="yolov8n.pt", config_path="roi_config.json")
    
    logger.info("="*60)
    logger.info("HỆ THỐNG GIÁM SÁT THÔNG MINH - LOGIC ĐIỂM CHÂN (V3.0)")
    logger.info("="*60)
    
    # Biến trạng thái
    current_status = "UNKNOWN"
    total_missing_time = 0.0
    ALARM_DELAY_SECONDS = 5.0
    
    # Metrics
    last_log_time = time.time()
    last_inference_time = 0
    INFERENCE_INTERVAL = 0.15 
    
    last_frame_id = -1
    last_processed_time = time.time()
    detections = []
    real_camera_fps = 0
    unique_frame_count = 0
    total_data_bytes = 0

    while True:
        ret, frame, frame_id = streamer.read()
        
        if ret and frame is not None:
            # Bỏ qua nếu lag (Hình cũ)
            if frame_id == last_frame_id:
                time.sleep(0.005)
                continue
            
            now = time.time()
            time_delta = now - last_processed_time
            last_processed_time = now
            unique_frame_count += 1
            last_frame_id = frame_id
            total_data_bytes += frame.nbytes 
            
            # 2. RUN AI
            if (now - last_inference_time > INFERENCE_INTERVAL):
                detections = engine.detect_people(frame)
                last_inference_time = now
            
            # 3. SAFETY LOGIC
            people_in_roi = [d for d in detections if d["is_safe"]]
            count_in_roi = len(people_in_roi)
            
            if count_in_roi >= 1:
                total_missing_time = 0.0
                new_status = "SAFE"
            else:
                total_missing_time += time_delta
                new_status = "WARNING" if (total_missing_time >= ALARM_DELAY_SECONDS) else (current_status if current_status != "UNKNOWN" else "SAFE")

            if new_status != current_status:
                logger.info(f"\n[EVENT] >>> {time.strftime('%H:%M:%S')} | {current_status} -> {new_status}")
                current_status = new_status

            # 4. GIAO DIỆN
            display_frame = frame.copy()
            roi_color = (0, 255, 0) if current_status == "SAFE" else (0, 0, 255)
            
            # Vẽ ROI
            if engine.roi_polygon is not None:
                cv2.polylines(display_frame, [engine.roi_polygon], True, roi_color, 3)

            # Vẽ người và "Điểm chân"
            for det in detections:
                color = (0, 255, 0) if det["is_safe"] else (0, 255, 255)
                cv2.rectangle(display_frame, (det["box"][0], det["box"][1]), (det["box"][2], det["box"][3]), color, 2)
                
                # Vẽ điểm CHÂN để debug
                fx = int((det["box"][0] + det["box"][2]) / 2)
                fy = det["box"][3]
                cv2.circle(display_frame, (fx, fy), 8, color, -1)
                cv2.putText(display_frame, f"Conf: {det['conf']:.2f}", (det["box"][0], det["box"][1]-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Banner
            status_text = f"OP: OK ({count_in_roi}/{len(detections)})" if current_status == "SAFE" else "OP: MISSING!"
            cv2.rectangle(display_frame, (0, 0), (520, 65), roi_color, -1)
            cv2.putText(display_frame, status_text, (20, 48), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

            # Dashboard in Log
            if now - last_log_time > 5:
                real_camera_fps = unique_frame_count / (now - last_log_time)
                logger.info("-" * 40)
                logger.info(f"DASHBOARD REPORT | FPS: {real_camera_fps:.1f} | STATUS: {current_status}")
                if total_missing_time > 0:
                    logger.info(f"Missing: {total_missing_time:.1f}s / {ALARM_DELAY_SECONDS}s")
                logger.info("-" * 40)
                last_log_time = now
                unique_frame_count = 0

            # Show
            h, w = display_frame.shape[:2]
            display_frame = cv2.resize(display_frame, (1280, int(1280 * h / w)))
            cv2.imshow("Smart Safety Monitor V3.0", display_frame)

        if cv2.waitKey(1) == 27:
            break

    streamer.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()