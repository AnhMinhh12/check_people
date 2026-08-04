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
    GRID_JPEG_QUALITY, GRID_FRAME_SIZE, GRID_EMIT_HZ
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

    def run(self):
        self.running = True
        self.streamer.start()

        # Quản lý thời gian vắng mặt độc lập cho từng vùng
        zone_timers = {} # {machine_name: seconds}
        zone_screenshots = {} # {machine_name: filename}
        occupied_confirm_timers = {} # {machine_name: seconds} - Bộ đệm xác nhận người quay lại
        absent_grace_timers = {} # {machine_name: seconds} - Bộ đệm chống nháy
        
        last_loop_time = time.time()
        last_emit_time = 0
        last_ai_time = 0
        last_heartbeat_time = time.time() # Heartbeat 10 phút/lần
        last_detections = []
        fps_avg = 0
        self.logger.info(">>> [BAT DAU] He thong Warden AI da san sang va dang giam sat!")
        
        # 1. Tai cau hinh vung tu Database (Professional Sync)
        self.refresh_zones_from_db()

        last_frame_id = -1
        res_logged = False

        while self.running:
            loop_start = time.time()
            
            # --- KIỂM TRA TẦN SUẤT XỬ LÝ ---
            now = time.time()
            
            # --- HEARTBEAT 10 PHUT/LAN DE BIET MAY VAN SONG ---
            if now - last_heartbeat_time > 600:
                db_ok = self.event_repo.check_connection()
                if db_ok:
                    self.refresh_zones_from_db() # Cap nhat lai ID may neu co thay doi tu Web
                self.logger.info(f"HBT [CAM {self.camera_id}] May dang chay. Ket noi DB: {'OK' if db_ok else 'FAILED'}")
                last_heartbeat_time = now

            needs_ai = (now - last_ai_time >= (1.0 / self.ai_max_fps))
            emit_interval = 0.25 # 4 FPS cho Web
            needs_web = (now - last_emit_time >= emit_interval)

            # --- ĐỌC HÌNH ---
            t_read_start = time.perf_counter()
            copy_needed = needs_ai or needs_web
            ret, frame, frame_id = self.streamer.read(copy=copy_needed)
            t_read_ms = (time.perf_counter() - t_read_start) * 1000

            if not ret or frame is None:
                time.sleep(0.01) 
                continue
            
            # Log độ phân giải 1 lần duy nhất để debug CPU
            if not res_logged:
                h_cam, w_cam = frame.shape[:2]
                self.logger.info(f"📊 [CAM {self.camera_id}] Do phan giai nhan: {w_cam}x{h_cam}")
                res_logged = True

            if frame_id == last_frame_id:
                # Không có hình mới, chờ một chút để giảm CPU
                time.sleep(0.005)
                continue

            last_frame_id = frame_id

            # Cập nhật trạng thái kết nối
            if self.system_data["camera_connected"] != ret:
                self.system_data["camera_connected"] = ret
                self.socketio.emit(f'stats_update_{self.camera_id}', self.system_data)

            # --- XỬ LÝ AI ---
            # Chỉ tính toán logic và ROI khi có kết quả AI mới (Tiết kiệm CPU cực lớn)
            t_ai_ms = 0.0
            if needs_ai:
                t_ai_start = time.perf_counter()
                frame_small_ai = cv2.resize(frame, (640, 360))
                last_detections = self.engine.detect_people(frame_small_ai)
                t_ai_ms = (time.perf_counter() - t_ai_start) * 1000
                last_ai_time = now
                
                # Logic vi phạm đa vùng
                time_delta = now - (last_loop_time if last_loop_time > 0 else now)
                last_loop_time = now

                # 1. Xác định những máy nào có người
                occupied_zones = set()
                for det in last_detections:
                    for zone_name in det.get("zones", []):
                        occupied_zones.add(zone_name)

                # 2. Cập nhật trạng thái cho từng vùng (Tính toán trước để Snapshot có đủ dữ liệu)
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

                    # Lấy thời gian thực tế để xử lý sự kiện
                    real_missing_time = zone_timers[z_name]

                    if not is_occupied:
                        # --- CHỐNG NHÁY (GRACE PERIOD) ---
                        # Nếu vừa mất dấu người, chờ 2.0s trước khi thực sự coi là vắng mặt
                        absent_grace_timers[z_name] += time_delta
                        
                        if absent_grace_timers[z_name] >= 2.0:
                            # Đã quá thời gian ân hạn, thực sự tính là vắng mặt
                            occupied_confirm_timers[z_name] = 0.0
                            zone_timers[z_name] += time_delta
                            real_missing_time = zone_timers[z_name]

                            if zone_timers[z_name] >= self.alarm_delay: z_status = STATUS_VIOLATION
                            elif zone_timers[z_name] >= 1.0: z_status = STATUS_LEFT
                            else: z_status = STATUS_SAFE
                        else:
                            # Đang trong thời gian ân hạn, giữ nguyên trạng thái và bộ đệm trước đó
                            z_status = STATUS_SAFE if zone_timers[z_name] < 1.0 else STATUS_LEFT
                            if zone_timers[z_name] >= self.alarm_delay: z_status = STATUS_VIOLATION
                    else:
                        # --- CÓ NGƯỜI: XÁC NHẬN AN TOÀN ---
                        absent_grace_timers[z_name] = 0.0 # Thấy người là reset ngay grace timer
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
                        "real_missing_time": real_missing_time, # Dùng cho Phase 3
                        "worker_count": len(people_in_this_zone)
                    })

                # 3. Xử lý Sự kiện (Events) dựa trên trạng thái đã tính toán
                for z_stat in zones_stats:
                    z_name = z_stat["name"]
                    z_status = z_stat["status"]
                    z_time = z_stat["real_missing_time"]

                    # A. Phát hiện VI PHẠM MỚI
                    if z_status == STATUS_VIOLATION and zone_screenshots[z_name] is None:
                        # --- TỔNG HỢP DANH SÁCH MÁY ĐANG VI PHẠM TẠI CÙNG THỜI ĐIỂM ---
                        all_violating = [z["name"] for z in zones_stats if z["status"] == STATUS_VIOLATION]
                        machines_str = ", ".join(all_violating) # Giữ nguyên dấu và hoa/thường từ User

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
                        
                        # --- THÔNG BÁO WEB CẬP NHẬT LỊCH SỬ ---
                        self.socketio.emit('new_violation', {'camera_id': self.camera_id, 'zone': z_name})

                        # --- GỬI THÔNG BÁO GMAIL ---
                        if snapshot_name:
                            full_snapshot_path = os.path.join(settings.VIOLATIONS_DIR, snapshot_name)
                            gmail_notifier.send_violation_alert(
                                camera_name=self.name,
                                zone_name=z_name,
                                duration=round(z_time, 1),
                                timestamp=datetime.now(timezone(timedelta(hours=7))).strftime("%H:%M:%S %d/%m/%Y"),
                                snapshot_path=full_snapshot_path
                            )

                    # B. Kết thúc vi phạm (Dọn dẹp screenshot lưu trữ)
                    elif z_status == STATUS_SAFE and zone_screenshots[z_name] is not None:
                        e_id = self.active_event_ids.get(z_name)
                        if e_id:
                            self.event_repo.finish_event(e_id, round(z_time, 1))
                            self.logger.info(f"ĐÃ AN TOÀN: {z_name} đã trở lại sau {round(z_time, 1)}s.")
                            self.socketio.emit('new_violation', {'camera_id': self.camera_id, 'zone': z_name, 'finished': True})
                        
                        zone_screenshots[z_name] = None
                        self.active_event_ids[z_name] = None

                # Cập nhật system_data tổng để hiển thị dashboard
                self.system_data["zones_stats"] = zones_stats
                self.system_data["workers_in_roi"] = len(occupied_zones)
                
                # Trạng thái tổng quát của Camera
                if any(z["status"] == STATUS_VIOLATION for z in zones_stats):
                    self.system_data["status"] = STATUS_VIOLATION
                    self.system_data["status_code"] = 2
                elif any(z["status"] == STATUS_LEFT for z in zones_stats):
                    self.system_data["status"] = STATUS_LEFT
                    self.system_data["status_code"] = 1
                else:
                    self.system_data["status"] = STATUS_SAFE
                    self.system_data["status_code"] = 0

            # --- GỬI DỮ LIỆU DASHBOARD ---
            # Điều chỉnh tần suất emit theo chế độ (Grid mode chậm hơn để tiết kiệm băng thông)
            active_emit_interval = GRID_EMIT_HZ if self.is_grid_mode else emit_interval
            if now - last_emit_time >= active_emit_interval:
                img_base64 = None
                if self.is_focused:
                    try:
                        # TỔI ƯU TỐI THƯỢNG: Chuẩn hóa 640x360 cho cả hai chế độ để đảm bảo mượt mà 100%
                        # (Giảm từ 960x540 xuống 640x360 để máy Local cũng chạy được như Server)
                        frame_for_web = cv2.resize(frame, GRID_FRAME_SIZE)
                        
                        # Sử dụng chất lượng 75 cho Focused, 60 cho Grid
                        quality = DASHBOARD_JPEG_QUALITY if not self.is_grid_mode else GRID_JPEG_QUALITY
                        ret_enc, buffer = cv2.imencode('.jpg', frame_for_web, [cv2.IMWRITE_JPEG_QUALITY, quality])
                        
                        if ret_enc:
                            img_base64 = base64.b64encode(buffer).decode('utf-8')
                            if not hasattr(self, '_log_count'): self._log_count = 0
                            self._log_count += 1
                            if self._log_count % 40 == 0: # Giảm log để không treo console
                                self.logger.debug(f"📸 [EMIT] Cam {self.camera_id} | Size: {len(img_base64)} | Focus: {self.is_focused} | Grid: {self.is_grid_mode}")
                        else:
                            self.logger.error(f"❌ [LỖI] Cam {self.camera_id} - Không thể nén ảnh JPEG")
                    except Exception as e:
                        self.logger.error(f"❌ [LỖI] Cam {self.camera_id} - Xử lý ảnh thất bại: {e}")

                max_missing = max([z["missing_time"] for z in zones_stats]) if zones_stats else 0.0

                # --- TÍNH FPS THEO CHU KỲ XỬ LÝ THẬT ---
                if not hasattr(self, '_fps_ema'): self._fps_ema = self.ai_max_fps
                loop_duration = time.time() - loop_start
                curr_fps = 1.0 / (loop_duration + 1e-6)
                self._fps_ema = self._fps_ema * 0.9 + curr_fps * 0.1

                self.system_data.update({
                    "total_workers": len(last_detections),
                    "status": self.system_data.get("status", STATUS_WAITING),
                    "status_code": self.system_data.get("status_code", 0),
                    "missing_time": round(max_missing, 1),
                    "latest_detections": last_detections,
                    "all_rois": [z["points"] for z in self.engine.roi_zones],
                    "image": img_base64,
                    "zones_stats": zones_stats,
                    "alarm_threshold": self.alarm_delay,
                    "camera_id": self.camera_id
                })

                if not self.is_focused and "image" in self.system_data:
                    del self.system_data["image"]
                
                self.socketio.emit(f'stats_update_{self.camera_id}', self.system_data)
                last_emit_time = now

            # --- NGHỈ VÀ TÍNH FPS ---
            loop_duration = time.time() - loop_start
            # Nếu không cần làm gì nhiều, nghỉ lâu hơn một chút
            target_fps = 30.0
            wait_time = max(0.002, (1.0 / target_fps) - loop_duration)
            time.sleep(wait_time)

            total_duration = time.time() - loop_start
            current_fps = 1.0 / (total_duration + 0.0001)
            fps_avg = fps_avg * 0.9 + current_fps * 0.1

            # --- LOG CHUẨN ĐOÁN MỖI 10 GIÂY ---
            if getattr(self, '_last_diag_log', 0) < now - 10.0:
                self.logger.info(f"⏱️ [CPU DIAGNOSTIC - CAM {self.camera_id}] Toc do keo Frame: {t_read_ms:.1f} ms | Phan tich AI: {t_ai_ms:.1f} ms | Vong lap mat tong: {total_duration*1000:.1f} ms")
                self._last_diag_log = now



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
