import threading
import time
import cv2
import logging
import base64
import os
from datetime import datetime
from src.core.camera_stream import CameraStreamer
from src.core.ai_engine import AIEngine



class AIWorker(threading.Thread):
    def __init__(self, camera_id, name, rtsp_url, model_instance, config_path, alarm_delay, db_manager, socketio):
        super().__init__()
        self.camera_id = camera_id
        self.name = name
        self.streamer = CameraStreamer(rtsp_url)
        # Mỗi camera có file cấu hình ROI riêng trong thư mục data/
        self.config_path = config_path
        self.engine = AIEngine(model_instance=model_instance, config_path=self.config_path)
        self.db_manager = db_manager
        self.socketio = socketio
        self.alarm_delay = alarm_delay
        self.running = False
        self.daemon = True
        
        # Setup Logger riêng cho từng Camera
        logs_dir = os.getenv("LOGS_DIR", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        self.logger = logging.getLogger(f"AIWorker_CAM_{camera_id}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(f"{logs_dir}/camera_{camera_id}.log", encoding='utf-8')
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(fh)
            self.logger.propagate = False  # Ngăn log tràn ra màn hình console chung
        
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
        
        self.logger.info(">>> [BẮT ĐẦU] Hệ thống Warden AI đã sẵn sàng và đang giám sát!")

        while self.running:
            loop_start = time.time()
            ret, frame, frame_id = self.streamer.read()
            
            # Đồng bộ kết nối Camera
            if self.system_data["camera_connected"] != ret:
                self.system_data["camera_connected"] = ret
                self.socketio.emit(f'stats_update_{self.camera_id}', self.system_data)
                if ret: self.logger.info(f">>> [CAM {self.camera_id}] Camera {self.name} đã kết nối!")
                else: self.logger.warning(f">>> [CAM {self.camera_id}] Mất tín hiệu {self.name}!")

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
                    current_violation_img = self._save_violation_snapshot(frame, detections)
                    screenshot_taken = True
            else:
                # Nếu trước đó đang có vi phạm, giờ quay lại -> CHỐT SỔ
                if screenshot_taken and current_violation_img:
                    self.db_manager.add_violation(self.camera_id, 
                                                 current_violation_img, 
                                                 round(total_missing_time, 1))
                    self.logger.info(f"[CAM {self.camera_id}] Kết thúc vi phạm: {round(total_missing_time, 1)}s")

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
                    "roi_on_server": self.engine.current_roi.tolist() if self.engine.current_roi is not None else [],
                    "camera_id": self.camera_id,
                    "camera_name": self.name,
                    "alarm_threshold": self.alarm_delay
                })
                self.socketio.emit(f'stats_update_{self.camera_id}', self.system_data)
                last_emit_time = now

    def _save_violation_snapshot(self, frame, detections):
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
            cv2.imwrite(os.path.join("data", "violations", filename), save_frame)
            return filename
        except Exception as e:
            self.logger.error(f"Lỗi chụp ảnh hiện trường: {e}")
            return None

    def stop(self):
        self.running = False
        self.streamer.stop()
