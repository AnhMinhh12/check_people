import cv2
import time
import threading
import logging
from datetime import datetime
from src.core.camera_stream import CameraStreamer
from src.core.ai_engine import AIEngine

logger = logging.getLogger("WardenApp.Service")

class AIWorker(threading.Thread):
    def __init__(self, rtsp_url, model_path, config_path, alarm_delay, db_manager, socketio):
        super().__init__()
        self.streamer = CameraStreamer(rtsp_url)
        self.engine = AIEngine(model_path=model_path, config_path=config_path)
        self.alarm_delay = alarm_delay
        self.db_manager = db_manager
        self.socketio = socketio
        
        self.running = True
        self.screenshot_taken = False
        self.current_violation_id = None
        self.latest_frame = None
        self.lock = threading.Lock()
        
        self.system_data = {
            "status": "ĐANG CHỜ",
            "workers_in_roi": 0,
            "total_workers": 0,
            "missing_time": 0.0,
            "fps": 0.0,
            "camera_connected": True,
            "original_resolution": [640, 360]
        }
        
        # Cập nhật độ phân giải gốc
        if self.engine.roi_mask is not None:
             h, w = self.engine.roi_mask.shape
             self.system_data["original_resolution"] = [w, h]

    def get_latest_frame(self):
        with self.lock:
            return self.latest_frame

    def get_system_data(self):
        with self.lock:
            return self.system_data.copy()

    def run(self):
        self.streamer.start()
        
        last_frame_id = -1
        last_processed_time = time.time()
        last_inference_time = 0
        INFERENCE_INTERVAL = 0.12 
        
        unique_frame_count = 0
        last_stats_time = time.time()
        detections = []
        current_status = "ĐANG CHỜ"
        total_missing_time = 0.0

        while self.running:
            ret, frame, frame_id = self.streamer.read()
            
            # Kiểm tra trạng thái kết nối
            with self.lock:
                if self.system_data.get("camera_connected") != ret:
                    self.system_data["camera_connected"] = ret
                    self.socketio.emit('stats_update', self.system_data)

            if not ret or frame is None:
                time.sleep(0.1)
                continue

            if frame_id == last_frame_id:
                time.sleep(0.005)
                continue

            now = time.time()
            time_delta = now - last_processed_time
            last_processed_time = now
            unique_frame_count += 1
            last_frame_id = frame_id

            # 1. AI Inference
            if (now - last_inference_time > INFERENCE_INTERVAL):
                detections = self.engine.detect_people(frame)
                last_inference_time = now

            # 2. Vẽ Dashboard
            display_frame = frame.copy()
            people_in_roi = [d for d in detections if d["is_safe"]]
            count_in_roi = len(people_in_roi)
            
            temp_status = "AN TOÀN"
            if count_in_roi < 1:
                item_missing_time = total_missing_time + time_delta
                if item_missing_time >= self.alarm_delay:
                    temp_status = "CẢNH BÁO"
                else:
                    temp_status = current_status if current_status != "ĐANG CHỜ" else "AN TOÀN"
            
            roi_color = (0, 255, 0) if temp_status == "AN TOÀN" else (0, 0, 255)
            if self.engine.roi_polygon is not None:
                cv2.polylines(display_frame, [self.engine.roi_polygon], True, roi_color, 2)
            
            for det in detections:
                color = (0, 255, 0) if det["is_safe"] else (0, 255, 255)
                cv2.rectangle(display_frame, (det["box"][0], det["box"][1]), (det["box"][2], det["box"][3]), color, 2)
                # Bút chì đầu người
                fx, fy = int((det["box"][0] + det["box"][2]) / 2), det["box"][3]
                cv2.circle(display_frame, (fx, fy), 5, color, -1)

            # 3. Safety Logic
            if count_in_roi >= 1:
                total_missing_time = 0.0
                new_status = "AN TOÀN"
                self.screenshot_taken = False
                self.current_violation_id = None
            else:
                total_missing_time += time_delta
                new_status = "CẢNH BÁO" if (total_missing_time >= self.alarm_delay) else (current_status if current_status != "ĐANG CHỜ" else "AN TOÀN")
                
                if total_missing_time >= self.alarm_delay:
                    if not self.screenshot_taken:
                        violation_data = self.db_manager.save_violation(display_frame, total_missing_time)
                        if violation_data:
                            self.current_violation_id = violation_data.get("id")
                            self.socketio.emit('new_violation', violation_data)
                        self.screenshot_taken = True
                    elif self.current_violation_id:
                        self.db_manager.update_duration(self.current_violation_id, total_missing_time)
                        self.socketio.emit('violation_update', {"id": self.current_violation_id, "duration": round(total_missing_time, 1)})

            if new_status != current_status:
                current_status = new_status
                msg = f"{time.strftime('%H:%M:%S')} | Trạng thái: {new_status}"
                self.socketio.emit('status_update', {"status": new_status, "log": msg})

            # Update Stats mỗi 0.5s
            if now - last_stats_time > 0.5:
                fps = unique_frame_count / (now - last_stats_time)
                with self.lock:
                    self.system_data.update({
                        "status": current_status,
                        "workers_in_roi": count_in_roi,
                        "total_workers": len(detections),
                        "missing_time": round(total_missing_time, 1),
                        "fps": round(fps, 1)
                    })
                self.socketio.emit('stats_update', self.system_data)
                last_stats_time = now
                unique_frame_count = 0

            with self.lock:
                self.latest_frame = display_frame

    def stop(self):
        self.running = False
        self.streamer.stop()
