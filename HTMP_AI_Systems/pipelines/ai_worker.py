"""
pipelines/ai_worker.py — AI Worker Thread: xử lý logic giám sát cho từng camera

Kiến trúc HTMP_AI_Systems:
  - Sử dụng ViolationRepository (Repository Pattern) thay cho DatabaseManager
  - Logging qua core.logging.get_camera_logger
  - Cấu hình qua core.config.settings
"""
import threading
import time
import cv2
import base64
import os
import numpy as np
from datetime import datetime, timezone, timedelta
from core.constants import (
    STATUS_WAITING, STATUS_SAFE, STATUS_LEFT, STATUS_VIOLATION, 
    DASHBOARD_JPEG_QUALITY, DASHBOARD_EMIT_HZ, DEFAULT_STATUS_BUFFER_SEC,
    DEFAULT_ABSENT_BUFFER_SEC, GRID_JPEG_QUALITY, GRID_FRAME_SIZE, GRID_EMIT_HZ
)
from db.models import Zone
from pipelines.camera_stream import CameraStreamer
from services.ai_engine import AIEngine
from core.logging import get_camera_logger
from core.config import settings
from integrations.gmail import gmail_notifier


class AIWorker(threading.Thread):
    def __init__(self, camera_id, name, rtsp_url, model_instance, config_path, alarm_delay, ai_max_fps, event_repo, zone_repo, socketio):
        super().__init__()
        self.camera_id = camera_id
        self.name = name
        self.streamer = CameraStreamer(rtsp_url)
        self.config_path = config_path
        self.engine = AIEngine(model_instance=model_instance, config_path=self.config_path)
        self.event_repo = event_repo
        self.zone_repo = zone_repo
        self.socketio = socketio
        self.alarm_delay = alarm_delay
        self.ai_max_fps = ai_max_fps
        self.running = False
        self.daemon = True
        
        # Mapping để link Event -> Zone ID
        self.zone_name_to_id = {} 

        # Logger riêng cho Camera (qua module core.logging)
        self.logger = get_camera_logger(camera_id, name)

        # Dashboard Data
        self.system_data = {
            "workers_in_roi": 0,
            "people_count": 0,
            "total_workers": 0,
            "status": STATUS_WAITING,
            "missing_time": 0.0,
            "fps": 0.0,
            "camera_connected": False,
            "image": None
        }
        self.is_focused = False
        self.is_grid_mode = False   # Chế độ Live Grid (ảnh nhỏ, FPS thấp)
        self.active_event_ids = {} # {zone_name: event_id} 

        # Shared states between AI thread and Emit thread
        self.last_detections = []
        self.zones_stats = []
        self.workers_in_roi = 0
        self.global_status = STATUS_WAITING
        self.global_status_code = 3
        self.state_lock = threading.Lock()
        self._fps_ema = ai_max_fps 

    def run(self):
        self.running = True
        self.streamer.start()

        self.logger.info(">>> [BAT DAU] He thong Warden AI da san sang va dang giam sat!")
        
        # 1. Tai cau hinh vung tu Database
        self.refresh_zones_from_db()

        # 2. Khoi dong AI Thread chay song song
        self.ai_thread = threading.Thread(target=self._ai_loop, daemon=True)
        self.ai_thread.start()

        last_emit_time = 0
        res_logged = False

        while self.running:
            loop_start = time.time()
            now = time.time()

            # --- ĐỌC HÌNH ---
            ret, frame, frame_id = self.streamer.read(copy=False)

            # Cập nhật trạng thái kết nối
            if self.system_data["camera_connected"] != ret:
                self.system_data["camera_connected"] = ret
                self.socketio.emit(f'stats_update_{self.camera_id}', self.system_data)

            if not ret or frame is None:
                time.sleep(0.01)
                continue

            if not res_logged:
                h_cam, w_cam = frame.shape[:2]
                self.logger.info(f"📊 [CAM {self.camera_id}] Do phan giai nhan: {w_cam}x{h_cam}")
                res_logged = True

            # Xác định khoảng thời gian emit theo chế độ
            # Focused: 10 FPS (0.1s), Grid: 4 FPS (0.25s), Idle/Background: 1 FPS (1.0s)
            if self.is_grid_mode:
                active_emit_interval = 0.25  # 4 FPS
            elif self.is_focused:
                active_emit_interval = 0.1   # 10 FPS
            else:
                active_emit_interval = 1.0   # 1 FPS (Không stream ảnh để tiết kiệm tối đa)

            if now - last_emit_time >= active_emit_interval:
                img_base64 = None
                if self.is_focused:
                    try:
                        # Chuẩn hóa 640x360 cho cả hai chế độ để đảm bảo mượt mà 100%
                        frame_for_web = cv2.resize(frame, GRID_FRAME_SIZE)
                        
                        # Sử dụng chất lượng 75 cho Focused, 60 cho Grid
                        quality = DASHBOARD_JPEG_QUALITY if not self.is_grid_mode else GRID_JPEG_QUALITY
                        ret_enc, buffer = cv2.imencode('.jpg', frame_for_web, [cv2.IMWRITE_JPEG_QUALITY, quality])
                        
                        if ret_enc:
                            img_base64 = base64.b64encode(buffer).decode('utf-8')
                        else:
                            self.logger.error(f"❌ [LỖI] Cam {self.camera_id} - Không thể nén ảnh JPEG")
                    except Exception as e:
                        self.logger.error(f"❌ [LỖI] Cam {self.camera_id} - Xử lý ảnh thất bại: {e}")

                # Copy states từ AI Thread dưới lock bảo vệ
                with self.state_lock:
                    last_detections = list(self.last_detections)
                    zones_stats = list(self.zones_stats)
                    workers_in_roi = self.workers_in_roi
                    global_status = self.global_status
                    global_status_code = self.global_status_code

                max_missing = max([z["missing_time"] for z in zones_stats]) if zones_stats else 0.0

                self.system_data.update({
                    "workers_in_roi": workers_in_roi,
                    "people_count": len(last_detections),
                    "total_workers": len(last_detections),
                    "status": global_status,
                    "status_code": global_status_code,
                    "missing_time": round(max_missing, 1),
                    "latest_detections": last_detections,
                    "all_rois": [z["points"] for z in self.engine.roi_zones],
                    "image": img_base64,
                    "zones_stats": zones_stats,
                    "alarm_threshold": self.alarm_delay,
                    "camera_id": self.camera_id,
                    "fps": round(self._fps_ema, 1)
                })

                if not self.is_focused and "image" in self.system_data:
                    del self.system_data["image"]
                
                self.socketio.emit(f'stats_update_{self.camera_id}', self.system_data)
                last_emit_time = now

            # Sleep ngắn để tránh spin loop và giữ phản hồi nhanh
            loop_duration = time.time() - loop_start
            wait_time = max(0.005, 0.033 - loop_duration) # cap ở ~30 FPS loop speed
            time.sleep(wait_time)

    def _ai_loop(self):
        zone_timers = {} # {machine_name: seconds}
        zone_screenshots = {} # {machine_name: filename}
        occupied_confirm_timers = {} # {machine_name: seconds}
        absent_grace_timers = {} # {machine_name: seconds}
        
        last_loop_time = time.time()
        last_ai_time = 0
        last_heartbeat_time = time.time()
        last_detections = []
        t_ai_ms = 0.0
        t_read_ms = 0.0

        while self.running:
            now = time.time()
            
            # --- HEARTBEAT 10 PHUT/LAN ---
            if now - last_heartbeat_time > 600:
                db_ok = self.event_repo.check_connection()
                if db_ok:
                    self.refresh_zones_from_db()
                self.logger.info(f"HBT [CAM {self.camera_id}] May dang chay. Ket noi DB: {'OK' if db_ok else 'FAILED'}")
                last_heartbeat_time = now

            # Chạy AI theo tần suất cấu hình AI_MAX_FPS
            if now - last_ai_time >= (1.0 / self.ai_max_fps):
                t_ai_start = time.perf_counter()
                
                # Đọc hình mới để AI phân tích
                ret, frame, frame_id = self.streamer.read(copy=True)
                t_read_ms = (time.perf_counter() - t_ai_start) * 1000
                
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue
                
                frame_small_ai = cv2.resize(frame, (640,360))
                last_detections = self.engine.detect_people(frame_small_ai)
                t_ai_ms = (time.perf_counter() - t_ai_start) * 1000 - t_read_ms
                last_ai_time = now
                
                time_delta = now - (last_loop_time if last_loop_time > 0 else now)
                last_loop_time = now

                # 1. Xác định những máy nào có người
                occupied_zones = set()
                for det in last_detections:
                    for zone_name in det.get("zones", []):
                        occupied_zones.add(zone_name)

                # 2. Cập nhật trạng thái cho từng vùng
                zones_stats = []
                for zone in self.engine.roi_zones:
                    z_name = zone["name"]
                    if z_name not in zone_timers:
                        zone_timers[z_name] = 0.0
                        zone_screenshots[z_name] = None
                        occupied_confirm_timers[z_name] = 0.0
                        absent_grace_timers[z_name] = 0.0
                    
                    is_occupied = z_name in occupied_zones
                    people_in_this_zone = [det for det in last_detections if z_name in det.get("zones", [])]
                    for det in people_in_this_zone: det["is_safe"] = True

                    real_missing_time = zone_timers[z_name]

                    if not is_occupied:
                        absent_grace_timers[z_name] += time_delta
                        
                        # Bộ đệm xác nhận vắng mặt 10 giây (chống miss/flicker AI khi cúi người hoặc che khuất)
                        if absent_grace_timers[z_name] >= DEFAULT_ABSENT_BUFFER_SEC:
                            occupied_confirm_timers[z_name] = 0.0
                            zone_timers[z_name] += time_delta
                            real_missing_time = zone_timers[z_name]

                            if zone_timers[z_name] >= self.alarm_delay: z_status = STATUS_VIOLATION
                            elif zone_timers[z_name] >= 1.0: z_status = STATUS_LEFT
                            else: z_status = STATUS_SAFE
                        else:
                            z_status = STATUS_SAFE if zone_timers[z_name] < 1.0 else STATUS_LEFT
                            if zone_timers[z_name] >= self.alarm_delay: z_status = STATUS_VIOLATION
                    else:
                        absent_grace_timers[z_name] = 0.0
                        occupied_confirm_timers[z_name] += time_delta
                        
                        if occupied_confirm_timers[z_name] >= DEFAULT_STATUS_BUFFER_SEC:
                            z_status = STATUS_SAFE
                            zone_timers[z_name] = 0.0 
                        else:
                            z_status = STATUS_LEFT if zone_timers[z_name] >= 1.0 else STATUS_SAFE
                            if zone_timers[z_name] >= self.alarm_delay: z_status = STATUS_VIOLATION

                    status_code = 0
                    if z_status == STATUS_LEFT: status_code = 1
                    elif z_status == STATUS_VIOLATION: status_code = 2
                    elif z_status == STATUS_WAITING: status_code = 3

                    zones_stats.append({
                        "name": z_name,
                        "status": z_status,
                        "status_code": status_code,
                        "missing_time": round(zone_timers[z_name], 1),
                        "real_missing_time": real_missing_time,
                        "worker_count": len(people_in_this_zone)
                    })

                # 3. Xử lý Sự kiện (Events)
                for z_stat in zones_stats:
                    z_name = z_stat["name"]
                    z_status = z_stat["status"]
                    z_time = z_stat["real_missing_time"]

                    if z_status == STATUS_VIOLATION and zone_screenshots[z_name] is None:
                        all_violating = [z["name"] for z in zones_stats if z["status"] == STATUS_VIOLATION]
                        machines_str = ", ".join(all_violating)

                        snapshot_name = self._save_violation_snapshot(frame, last_detections, zones_stats=zones_stats, violating_zone_name=z_name)
                        zone_screenshots[z_name] = snapshot_name
                        event_id = self.event_repo.add(
                            camera_id=self.camera_id,
                            zone_id=self.zone_name_to_id.get(z_name),
                            event_type="absence_violation",
                            filename=snapshot_name,
                            duration=round(z_time, 1),
                            machines=machines_str
                        )
                        self.active_event_ids[z_name] = event_id
                        self.socketio.emit('new_violation', {'camera_id': self.camera_id, 'zone': z_name})

                        if snapshot_name:
                            full_snapshot_path = os.path.join(settings.VIOLATIONS_DIR, snapshot_name)
                            gmail_notifier.send_violation_alert(
                                camera_name=self.name,
                                zone_name=z_name,
                                duration=round(z_time, 1),
                                timestamp=datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S %d/%m/%Y"),
                                snapshot_path=full_snapshot_path
                            )

                    elif z_status == STATUS_SAFE and zone_screenshots[z_name] is not None:
                        e_id = self.active_event_ids.get(z_name)
                        if e_id:
                            self.event_repo.finish_event(e_id, round(z_time, 1))
                            self.logger.info(f"ĐÃ AN TOÀN: {z_name} đã trở lại sau {round(z_time, 1)}s.")
                            self.socketio.emit('new_violation', {'camera_id': self.camera_id, 'zone': z_name, 'finished': True})
                        
                        zone_screenshots[z_name] = None
                        self.active_event_ids[z_name] = None

                # Cập nhật shared states dưới lock bảo vệ
                with self.state_lock:
                    self.last_detections = last_detections
                    self.zones_stats = zones_stats
                    self.workers_in_roi = len(occupied_zones)
                    
                    if any(z["status"] == STATUS_VIOLATION for z in zones_stats):
                        self.global_status = STATUS_VIOLATION
                        self.global_status_code = 2
                    elif any(z["status"] == STATUS_LEFT for z in zones_stats):
                        self.global_status = STATUS_LEFT
                        self.global_status_code = 1
                    else:
                        self.global_status = STATUS_SAFE
                        self.global_status_code = 0

                loop_duration = time.perf_counter() - t_ai_start
                curr_fps = 1.0 / (loop_duration + 1e-6)
                self._fps_ema = self._fps_ema * 0.9 + curr_fps * 0.1

                # --- LOG CHUẨN ĐOÁN MỖI 10 GIÂY ---
                if getattr(self, '_last_diag_log', 0) < now - 10.0:
                    self.logger.info(f"⏱️ [CPU DIAGNOSTIC - CAM {self.camera_id}] Toc do keo Frame: {t_read_ms:.1f} ms | Phan tich AI: {t_ai_ms:.1f} ms | Vong lap AI mat tong: {loop_duration*1000:.1f} ms")
                    self._last_diag_log = now

            time.sleep(0.01)



    def no_accent_vietnamese(self, s):
        """Chuyển đổi tiếng Việt có dấu sang không dấu (OpenCV FIX)"""
        s = s.replace("à", "a").replace("á", "a").replace("ạ", "a").replace("ả", "a").replace("ã", "a").replace("â", "a").replace("ầ", "a").replace("ấ", "a").replace("ậ", "a").replace("ẩ", "a").replace("ẫ", "a").replace("ă", "a").replace("ằ", "a").replace("ắ", "a").replace("ặ", "a").replace("ẳ", "a").replace("ẵ", "a")
        s = s.replace("è", "e").replace("é", "e").replace("ẹ", "e").replace("ẻ", "e").replace("ẽ", "e").replace("ê", "e").replace("ề", "e").replace("ế", "e").replace("ệ", "e").replace("ể", "e").replace("ễ", "e")
        s = s.replace("ì", "i").replace("í", "i").replace("ị", "i").replace("ỉ", "i").replace("ĩ", "i")
        s = s.replace("ò", "o").replace("ó", "o").replace("ọ", "o").replace("ỏ", "o").replace("õ", "o").replace("ô", "o").replace("ồ", "o").replace("ố", "o").replace("ộ", "o").replace("ổ", "o").replace("ỗ", "o").replace("ơ", "o").replace("ờ", "o").replace("ớ", "o").replace("ợ", "o").replace("ở", "o").replace("ỡ", "o")
        s = s.replace("ù", "u").replace("ú", "u").replace("ụ", "u").replace("ủ", "u").replace("ũ", "u").replace("ư", "u").replace("ừ", "u").replace("ứ", "u").replace("ự", "u").replace("ử", "u").replace("ữ", "u")
        s = s.replace("ỳ", "y").replace("ý", "y").replace("ỵ", "y").replace("ỷ", "y").replace("ỹ", "y")
        s = s.replace("đ", "d")
        s = s.replace("À", "A").replace("Á", "A").replace("Ạ", "A").replace("Ả", "A").replace("Ã", "A").replace("Â", "A").replace("Ầ", "A").replace("Ấ", "A").replace("Ậ", "A").replace("Ẩ", "A").replace("Ẫ", "A").replace("Ă", "A").replace("Ằ", "A").replace("Ắ", "A").replace("Ặ", "A").replace("Ẳ", "A").replace("Ẵ", "A")
        s = s.replace("È", "E").replace("É", "E").replace("Ẹ", "E").replace("Ẻ", "E").replace("Ẽ", "E").replace("Ê", "E").replace("Ề", "E").replace("Ế", "E").replace("Ệ", "E").replace("Ể", "E").replace("Ễ", "E")
        s = s.replace("Ì", "I").replace("Í", "I").replace("Ị", "I").replace("Ỉ", "I").replace("Ĩ", "I")
        s = s.replace("Ò", "O").replace("Ó", "O").replace("Ọ", "O").replace("Ỏ", "O").replace("Õ", "O").replace("Ô", "O").replace("Ồ", "O").replace("Ố", "O").replace("Ộ", "O").replace("Ổ", "O").replace("Ỗ", "O").replace("Ơ", "O").replace("Ờ", "O").replace("Ớ", "O").replace("Ợ", "O").replace("Ở", "O").replace("Ỡ", "O")
        s = s.replace("Ù", "U").replace("Ú", "U").replace("Ụ", "U").replace("Ủ", "U").replace("Ũ", "U").replace("Ư", "U").replace("Ừ", "U").replace("Ứ", "U").replace("Ự", "U").replace("Ử", "U").replace("Ữ", "U")
        s = s.replace("Ỳ", "Y").replace("Ý", "Y").replace("Ỵ", "Y").replace("Ỷ", "Y").replace("Ỹ", "Y")
        s = s.replace("Đ", "D")
        return s

    def _save_violation_snapshot(self, frame, detections, zones_stats=None, violating_zone_name=None):
        """Chụp ảnh hiện trường ngay lúc vi phạm và trả về tên file"""
        try:
            save_frame = frame.copy()
            h, w = save_frame.shape[:2]
            sx, sy = w / 640.0, h / 360.0

            # Bản đồ trạng thái hiện tại của các máy
            status_map = {z["name"]: z["status_code"] for z in (zones_stats or [])}

            # Vẽ TẤT CẢ các vùng ROI
            for zone in self.engine.roi_zones:
                pts = np.array(zone["points"], dtype=np.int32)
                scaled_poly = np.array([[int(p[0] * sx), int(p[1] * sy)] for p in pts], dtype=np.int32)
                
                z_name = zone["name"]
                z_status_code = status_map.get(z_name, 0)
                
                if not zones_stats and violating_zone_name and z_name == violating_zone_name:
                    z_status_code = 2

                if z_status_code == 2:
                    color = (0, 0, 255); thickness = 4
                elif z_status_code == 1:
                    color = (0, 215, 255); thickness = 3
                else:
                    color = (0, 255, 0); thickness = 2
                
                cv2.polylines(save_frame, [scaled_poly], True, color, thickness)
                # ĐÃ XÓA: Không vẽ tên máy tại vị trí ROI để tránh vướng víu (Theo yêu cầu)

            # Vẽ Bounding Box người
            for d in detections:
                box = d["box"]; bx1, by1, bx2, by2 = int(box[0]*sx), int(box[1]*sy), int(box[2]*sx), int(box[3]*sy)
                color = (0, 255, 0) if d["is_safe"] else (0, 255, 255)
                cv2.rectangle(save_frame, (bx1, by1), (bx2, by2), color, 2)

            # --- VẼ TIÊU ĐỀ: TỰ ĐỘNG XUỐNG DÒNG (WRAPPED TEXT) ---
            violating_names = [self.no_accent_vietnamese(z["name"]).upper() for z in (zones_stats or []) if z["status_code"] == 2]
            if not violating_names and violating_zone_name:
                violating_names = [self.no_accent_vietnamese(violating_zone_name).upper()]
            
            header = "VI PHAM TAI:"
            # Giảm kích thước tiêu đề (0.85) và độ dày (3)
            cv2.putText(save_frame, header, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 3)
            
            y_offset = 85
            line_text = ""
            for i, name in enumerate(violating_names):
                test_line = line_text + (", " if line_text else "") + name
                # Giới hạn khoảng 45 ký tự do cỡ chữ đã nhỏ hơn
                if len(test_line) > 45:
                    cv2.putText(save_frame, line_text + ",", (50, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                    y_offset += 40
                    line_text = name
                else:
                    line_text = test_line
            
            if line_text:
                cv2.putText(save_frame, line_text, (50, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"violation_{timestamp}.jpg"
            cv2.imwrite(os.path.join(settings.VIOLATIONS_DIR, filename), save_frame)
            return filename
        except Exception as e:
            self.logger.error(f"LOI CHUP ANH HIEN TRUONG: {e}")
            return None

    def reload_config(self):
        """Ép AI Worker nạp lại cấu hình vùng ngay lập tức"""
        self.refresh_zones_from_db()
        # Ép Engine nạp lại từ file JSON ngay (không đợi 2s)
        self.engine.load_config()
        self.logger.info(f"⚡ Đã nạp lại cấu hình ROI mới cho Camera {self.camera_id}")

    def refresh_zones_from_db(self):
        """Lấy danh sách vùng từ Database và cập nhật vào Engine"""
        try:
            db_zones = self.zone_repo.get_by_camera(self.camera_id)
            if db_zones:
                # 1. Cập nhật Mapping ID
                self.zone_name_to_id = {z["name"]: z["id"] for z in db_zones}
                
                # 2. Cập nhật vào Engine
                self.engine.update_zones(db_zones)
                self.logger.info(f"🔄 Đã đồng bộ {len(db_zones)} vùng từ Database vào AI Engine.")
            else:
                self.logger.warning(f"⚠️ Không tìm thấy vùng cấu hình trong Database cho Camera {self.camera_id}.")
        except Exception as e:
            self.logger.error(f"Lỗi đồng bộ vùng từ DB: {e}")

    def stop(self):
        self.running = False
        self.streamer.stop()
