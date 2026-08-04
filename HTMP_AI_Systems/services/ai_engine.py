"""
services/ai_engine.py — AI Engine: YOLO inference, ROI overlap, persistence buffer

Chuyển từ: src/core/ai_engine.py
Thay đổi: Import path cập nhật, sử dụng core.config.settings
"""
import cv2
import numpy as np
import json
import os
import logging
import time
from ultralytics import YOLO
import torch
from core.config import settings
from core.constants import DEFAULT_PERSISTENCE_FRAMES

logger = logging.getLogger("AIEngine")


import threading

# KHÓA TOÀN CỤC: Đảm bảo toàn dự án chỉ có đúng 1 tiến trình AI được chạy tại một thời điểm
# Đây là giải pháp "tuyệt chiêu" để ép Server 24 luồng không bị bùng nổ CPU
inference_lock = threading.Lock()

class AIEngine:
    def __init__(self, model_instance=None, model_path=None, config_path="roi_config.json"):
        # Đảm bảo các thư viện đã được khống chế luồng ngay từ khi khởi tạo Engine con
        try:
            import torch
            torch.set_num_threads(1)
            cv2.setNumThreads(1)
        except: pass

        # Nếu đã có Model được nạp sẵn (Singleton), sử dụng nó để tiết kiệm RAM (V5.0 Optimization)
        if model_instance is not None:
            self.model = model_instance
            
            # --- FIX: Tự động nhận diện thiết bị cho cả model (.pt) và (.onnx) ---
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                self.device = 'cuda'
                try:
                    hw_name = torch.cuda.get_device_name(0)
                except:
                    hw_name = "NVIDIA GPU"
            else:
                self.device = 'cpu'
                hw_name = "CPU Core"
                # DEBUG CHI TIẾT
                logger.error("!!! [CẢNH BÁO] CUDA KHÔNG KHẢ DỤNG!")
                try:
                    import subprocess
                    smi = subprocess.check_output(['nvidia-smi'], encoding='utf-8')
                    logger.info(f"Nvidia-smi inside container:\n{smi}")
                except:
                    logger.error("Không thể chạy nvidia-smi trong container.")
                
            logger.info(f">>> [PHẦN CỨNG] AI Engine đang chạy trên: {hw_name} ({self.device})")
        else:
            final_model = model_path if model_path and os.path.exists(model_path) else settings.MODEL_PATH
            
            # KIỂM TRA CUDA TRƯỚC KHI KHỞI TẠO
            cuda_available = torch.cuda.is_available()
            if not cuda_available:
                logger.error("!!! CUDA_IS_AVAILABLE TRẢ VỀ FALSE. Đang sử dụng CPU.")
                self.device = 'cpu'
            else:
                self.device = 'cuda'
                logger.info(f"CUDA KHẢ DỤNG: {torch.cuda.get_device_name(0)}")

            try:
                # Ép YOLO/ONNX sử dụng cấu hình đơn luồng để tránh treo máy chủ cục bộ và giảm 100% CPU
                if self.device == 'cpu':
                    logger.info(">>> [TỐI ƯU] Giới hạn luồng AI trên CPU để bảo vệ hệ thống...")
                    torch.set_num_threads(1)
                else:
                    torch.set_num_threads(4) 
                
                self.model = YOLO(final_model, task="detect")
                # ÉP MODEL SANG DEVICE
                self.model.to(self.device)
                
                hw_name = torch.cuda.get_device_name(0) if self.device == 'cuda' else "CPU Core"
                logger.info(f">>> [KHỞI TẠO] Model: {final_model} | Thiết bị: {hw_name}")
            except Exception as e:
                logger.error(f"Lỗi khởi tạo AI: {e}")
                # Fallback an toàn (V5.4 Cleanup)
                fallback = settings.MODEL_PATH
                if os.path.exists(fallback):
                    self.model = YOLO(fallback)
                    self.model.to('cpu')
                else:
                    logger.critical("KHÔNG TÌM THẤY MÔ HÌNH AI NÀO ĐỂ CHẠY!")

        self.conf = settings.CONFIDENCE_THRESHOLD
        self.config_path = config_path
        self.last_config_mtime = 0
        self.last_config_check = 0
        self.roi_zones = []
        self.roi_mask = None
        self.current_roi = None

        # BỘ NHỚ TRÍ NHỚ TẠM (Chống nháy Bounding Box)
        self.memory = {}  # {id: {"box": [x1,y1,x2,y2], "safe": bool, "frames": int}}
        self.max_memory_frames = DEFAULT_PERSISTENCE_FRAMES * 6 # Ví dụ: 5 frames * 6 (~6 giây ở 5 FPS)

        self.load_config()

    def load_config(self):
        """Tải cấu hình ROI từ file JSON (Hỗ trợ định danh từng vùng)"""
        if os.path.exists(self.config_path):
            try:
                self.last_config_mtime = os.path.getmtime(self.config_path)
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    zones = config.get("roi_zones")
                    if not zones:
                        polys = config.get("roi_polygons")
                        if not polys:
                            pts = config.get("roi_points") or config.get("roi_polygon") or []
                            polys = [pts] if len(pts) > 0 else []
                        zones = [{"name": f"Vùng {i+1}", "points": p} for i, p in enumerate(polys)]
                    
                    self.update_zones(zones)
                logger.info(f"Đã tải {len(self.roi_zones)} vùng từ file {self.config_path}")
            except Exception as e:
                logger.error(f"Lỗi tải ROI config từ file: {e}")

    def update_zones(self, zones_data: list):
        """Cập nhật danh sách vùng từ dữ liệu thô (JSON hoặc DB)"""
        try:
            # Chuẩn hóa dữ liệu: Đảm bảo mỗi vùng luôn có cả 'points' và 'roi' để không lỗi KeyError
            normalized_zones = []
            for z in zones_data:
                pts = z.get("points") or z.get("roi")
                if pts:
                    z["points"] = pts
                    z["roi"] = pts
                    normalized_zones.append(z)
            
            self.roi_zones = normalized_zones
            self.roi_mask = None # Sẽ được build lại ở detect_people
            
            if len(self.roi_zones) > 0:
                self.current_roi = np.array(self.roi_zones[0]["points"], dtype=np.int32)
            else:
                self.current_roi = None
        except Exception as e:
            logger.error(f"Lỗi cập nhật vùng AI: {e}")

    def detect_people(self, frame):
        # Chỉ kiểm tra file cấu hình mỗi 2 giây để tránh lag Disk I/O
        now = time.time()
        if now - self.last_config_check > 2.0:
            self.last_config_check = now
            if os.path.exists(self.config_path):
                mtime = os.path.getmtime(self.config_path)
                if mtime > self.last_config_mtime:
                    self.load_config()
            else:
                # Nếu file không tồn tại nhưng trước đó đã có vùng, thì xóa sạch (Xử lý trường hợp xóa file)
                if len(self.roi_zones) > 0:
                    logger.warning(f"File cấu hình {self.config_path} đã bị xóa. Đang xóa sạch vùng ROI.")
                    self.update_zones([])
                    self.last_config_mtime = 0

        h, w = frame.shape[:2]
        if (self.roi_mask is None or self.roi_mask.shape != (h, w)) and len(self.roi_zones) > 0:
            self.roi_mask = np.zeros((h, w), dtype=np.uint8)
            scale_x, scale_y = w / 640.0, h / 360.0
            
            for zone in self.roi_zones:
                # Hỗ trợ cả trường 'points' (JSON) và 'roi' (DB)
                z_points = zone.get("points") or zone.get("roi")
                if not z_points: continue
                
                pts = np.array(z_points, dtype=np.int32)
                scaled_poly = np.array([[int(p[0] * scale_x), int(p[1] * scale_y)] for p in pts], dtype=np.int32)
                zone["_scaled_poly"] = scaled_poly
                
                # Tạo mask riêng cho vùng này
                zone_mask = np.zeros((h, w), dtype=np.uint8)
                cv2.fillPoly(zone_mask, [scaled_poly], 255)
                zone["_mask"] = zone_mask
                
                # Vẽ lên mask tổng
                cv2.fillPoly(self.roi_mask, [scaled_poly], 255)

        # SỬ DỤNG KHÓA TOÀN CỤC ĐỂ ÉP XẾP HÀNG (Dập tắt 8+ core CPU spike)
        # Chỉ 1 camera được phép chạy AI tại một thời điểm
        with inference_lock:
            results = self.model.track(frame, persist=True, classes=[0], conf=self.conf,
                                       verbose=False, device=self.device, imgsz=640)
        
        current_detections = []
        found_ids = set()

        if results and results[0].boxes is not None:
            for r in results[0].boxes:
                box = r.xyxy[0].cpu().numpy().astype(int)
                track_id = int(r.id[0].item()) if r.id is not None else -1

                x1, y1, x2, y2 = box
                # MẶC ĐỊNH: Nếu không có vùng ROI nào (xóa hết vùng), coi như AN TOÀN hết
                is_safe = True if len(self.roi_zones) == 0 else False
                matched_zones = []

                if self.roi_mask is not None:
                    # TÌM VÙNG PHỦ TỐI ƯU (MAX OVERLAP RATIO)
                    # Giúp bắt đúng máy ngay cả khi người cúi, nghiêng hoặc bị che chân
                    box_w, box_h = (x2 - x1), (y2 - y1)
                    person_area = float(box_w * box_h) + 1e-6
                    best_zone = None
                    max_ratio = 0.0

                    for zone in self.roi_zones:
                        if "_mask" in zone:
                            # Lấy mask của vùng này trong phạm vi box người
                            z_mask_crop = zone["_mask"][y1:y2, x1:x2]
                            overlap_px = np.count_nonzero(z_mask_crop == 255)
                            ratio = overlap_px / person_area
                            
                            if ratio > max_ratio:
                                max_ratio = ratio
                                best_zone = zone["name"]

                    # Ngưỡng tối thiểu 5%: Đảm bảo người thực sự đứng tại máy (không phải đi ngang qua)
                    if best_zone and max_ratio > 0.05:
                        is_safe = True
                        matched_zones.append(best_zone)

                detection = {
                    "box": [int(x1), int(y1), int(x2), int(y2)], 
                    "is_safe": is_safe, 
                    "zones": matched_zones
                }
                current_detections.append(detection)

                if track_id != -1:
                    found_ids.add(track_id)
                    self.memory[track_id] = {"detection": detection, "frames": 0}

        # XỬ LÝ HÀNH VI "NHÁY" - TRUY XUẤT TRÍ NHỚ
        missing_ids = [tid for tid in self.memory if tid not in found_ids]
        for tid in missing_ids:
            self.memory[tid]["frames"] += 1
            if self.memory[tid]["frames"] <= self.max_memory_frames:
                current_detections.append(self.memory[tid]["detection"])
            else:
                del self.memory[tid]

        # CHỐNG ĐẾM TRÙNG (NMS)
        final_detections = []
        current_detections.sort(key=lambda x: (x["box"][2] - x["box"][0]) * (x["box"][3] - x["box"][1]), reverse=True)
        for d in current_detections:
            is_redundant = False
            for f in final_detections:
                if self._check_overlap(d["box"], f["box"]):
                    is_redundant = True
                    break
            if not is_redundant:
                final_detections.append(d)

        return final_detections

    def _check_overlap(self, box1, box2):
        ax1, ay1, ax2, ay2 = box1
        bx1, by1, bx2, by2 = box2
        inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
        inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
        if inter_x1 < inter_x2 and inter_y1 < inter_y2:
            inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
            area1 = (ax2 - ax1) * (ay2 - ay1)
            if inter_area / float(area1) > 0.5:
                return True
        return False
