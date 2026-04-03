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
        current_violation_img = None
        fps_avg = 0
        
        logger.info(">>> [BẮT ĐẦU] Hệ thống Warden AI đã sẵn sàng và đang giám sát!")

        while self.running:
            loop_start = time.time()
            ret, frame, frame_id = self.streamer.read()
            
            # Đồng bộ kết nối Camera
            if self.system_data["camera_connected"] != ret:
                self.system_data["camera_connected"] = ret
                self.socketio.emit('stats_update', self.system_data)
                if ret: logger.info(">>> [STATUS] Camera đã kết nối!")
                else: logger.warning(">>> [STATUS] Mất tín hiệu Camera!")

            if not ret or frame is None:
                time.sleep(0.01)
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
                # Chỉ cảnh báo sau khi đã mất dấu thực sự trên 1.0 giây để tránh tình trạng "nháy"
                if total_missing_time >= 1.0:
                    status = "VI PHẠM" if total_missing_time >= self.alarm_delay else "RỜI VỊ TRÍ"
                else:
                    status = "AN TOÀN" # Đang trong 1 giây "đệm"
                
                if status == "VI PHẠM" and not screenshot_taken:
                    # Chụp ảnh bằng chứng ngay lúc vi phạm bắt đầu (từ 5s)
                    current_violation_img = self._save_violation_snapshot(frame, detections, count_in_roi)
                    screenshot_taken = True
            else:
                # Nếu trước đó đang có vi phạm, giờ quay lại -> CHỐT SỔ
                if screenshot_taken and current_violation_img:
                    self.db_manager.add_violation("Người vận hành rời khỏi vị trí", 
                                                 current_violation_img, 
                                                 round(total_missing_time, 1))
                    logger.info(f"Kết thúc vi phạm: Tổng thời gian vắng mặt {round(total_missing_time, 1)}s")

                total_missing_time = 0.0
                screenshot_taken = False
                current_violation_img = None

            # Tính toán FPS mượt mà
            duration = time.time() - loop_start
            current_fps = 1.0 / (duration + 0.001)
            fps_avg = fps_avg * 0.9 + current_fps * 0.1 # EMA (Exponential Moving Average)

            # Gửi dữ liệu Dashboard (Tăng lên 10Hz - 0.1s nếu AI đủ nhanh)
            emit_interval = 0.1 if fps_avg > 10 else 0.2
            if now - last_emit_time > emit_interval:
                # Resize ảnh sạch (không vẽ đè) trả về Dashboard
                mini_frame = cv2.resize(frame, (640, 360))
                # Nâng chất lượng JPEG lên 50 (cân bằng giữa độ nét và tốc độ)
                _, buffer = cv2.imencode('.jpg', mini_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                img_base64 = base64.b64encode(buffer).decode('utf-8')

                self.system_data.update({
                    "workers_in_roi": count_in_roi,
                    "people_count": count_in_roi,
                    "total_workers": len(detections),
                    "status": status,
                    "missing_time": round(total_missing_time, 1),
                    "fps": round(fps_avg, 1),
                    "image": img_base64,
                    "latest_detections": detections, # Gửi toạ độ người
                    "roi_on_server": self.engine.current_roi.tolist() if self.engine.current_roi is not None else []
                })
                self.socketio.emit('stats_update', self.system_data)
                last_emit_time = now

    def _save_violation_snapshot(self, frame, detections, count_in_roi):
        """Chụp ảnh hiện trường ngay lúc vi phạm và trả về tên file"""
        try:
            save_frame = frame.copy()
            if self.engine.current_roi is not None:
                cv2.polylines(save_frame, [self.engine.current_roi], True, (0, 0, 255), 3)
            for d in detections:
                box = d["box"]
                color = (0, 255, 0) if d["is_safe"] else (0, 255, 255)
                cv2.rectangle(save_frame, (box[0], box[1]), (box[2], box[3]), color, 3)

            cv2.putText(save_frame, "VI PHAM DANG DIEN RA", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"violation_{timestamp}.jpg"
            cv2.imwrite(os.path.join("violations", filename), save_frame)
            return filename
        except Exception as e:
            logger.error(f"Lỗi chụp ảnh hiện trường: {e}")
            return None

    def stop(self):
        self.running = False
        self.streamer.stop()
