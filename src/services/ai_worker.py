import threading
import time
import cv2
import logging
import base64
import os
from datetime import datetime
from src.core.camera_stream import CameraStreamer
from src.core.ai_engine import AIEngine

logger = logging.getLogger("AIWorker")

class AIWorker(threading.Thread):
    def __init__(self, rtsp_url, model_path, config_path, alarm_delay, db_manager, socketio):
        super().__init__()
        self.streamer = CameraStreamer(rtsp_url)
        self.engine = AIEngine(model_path, config_path)
        self.db_manager = db_manager
        self.socketio = socketio
        self.alarm_delay = alarm_delay
        self.running = False
        self.daemon = True
        
        # Dashboard Data
        self.system_data = {
            "workers_in_roi": 0,
            "people_count": 0,
            "total_workers": 0,
            "status": "ĐANG CHỜ",
            "missing_time": 0.0,
            "fps": 0.0,
            "camera_connected": False,
            "image": None
        }

    def run(self):
        self.running = True
        self.streamer.start()
        
        total_missing_time = 0.0
        last_loop_time = time.time()
        last_emit_time = 0
        screenshot_taken = False
        
        logger.info(">>> [BẮT ĐẦU] Hệ thống Warden AI đã sẵn sàng và đang giám sát!")

        while self.running:
            t0 = time.time()
            ret, frame, frame_id = self.streamer.read()
            
            # Đồng bộ kết nối Camera
            if self.system_data["camera_connected"] != ret:
                self.system_data["camera_connected"] = ret
                self.socketio.emit('stats_update', self.system_data)
                if ret: logger.info(">>> [STATUS] Camera đã kết nối!")
                else: logger.warning(">>> [STATUS] Mất tín hiệu Camera!")

            if not ret or frame is None:
                time.sleep(0.1)
                continue

            # Xử lý AI
            detections = self.engine.detect_people(frame)
            count_in_roi = sum(1 for d in detections if d["is_safe"])
            
            # Logic vi phạm
            now = time.time()
            time_delta = now - last_loop_time
            last_loop_time = now
            
            status = "AN TOÀN"
            if count_in_roi < 1:
                total_missing_time += time_delta
                status = "CẢNH BÁO" if total_missing_time >= self.alarm_delay else "CHƯA THẤY NGƯỜI"
                if status == "CẢNH BÁO" and not screenshot_taken:
                    self._save_violation(frame)
                    screenshot_taken = True
            else:
                total_missing_time = 0.0
                screenshot_taken = False

            # Vẽ Dashboard Frame (ROI + Boxes)
            roi_color = (0, 255, 0)
            if status == "CHƯA THẤY NGƯỜI": roi_color = (0, 255, 255)
            elif status == "CẢNH BÁO": roi_color = (0, 0, 255)
            
            display_frame = frame.copy()
            if self.engine.current_roi is not None:
                cv2.polylines(display_frame, [self.engine.current_roi], True, roi_color, 2)

            for d in detections:
                box = d["box"]
                color = (0, 255, 0) if d["is_safe"] else (0, 255, 255)
                cv2.rectangle(display_frame, (box[0], box[1]), (box[2], box[3]), color, 2)

            # Gửi dữ liệu Dashboard (5Hz - 0.2s) để mượt mà và rõ nét hơn
            if now - last_emit_time > 0.2:
                # Nâng chất lượng JPEG lên 60 để hình ảnh rõ hơn
                _, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                img_base64 = base64.b64encode(buffer).decode('utf-8')

                self.system_data.update({
                    "workers_in_roi": count_in_roi,
                    "people_count": count_in_roi,
                    "total_workers": len(detections),
                    "status": status,
                    "missing_time": round(total_missing_time, 1),
                    "fps": round(1.0 / (time.time() - t0 + 0.001), 1),
                    "image": img_base64
                })
                self.socketio.emit('stats_update', self.system_data)
                last_emit_time = now

    def _save_violation(self, frame):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"violation_{timestamp}.jpg"
            cv2.imwrite(os.path.join("violations", filename), frame)
            self.db_manager.add_violation("Không có người trong vùng ROI", filename)
            logger.info(f"Lịch sử: Đã lưu bằng chứng vi phạm {filename}")
        except Exception as e:
            logger.error(f"Lỗi lưu vi phạm: {e}")

    def stop(self):
        self.running = False
        self.streamer.stop()
