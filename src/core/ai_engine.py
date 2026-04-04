import cv2
import numpy as np
import json
import os
import logging
import time
from ultralytics import YOLO
import torch

logger = logging.getLogger("AIEngine")

class AIEngine:
    def __init__(self, model_instance=None, model_path=None, config_path="roi_config.json"):
        # Nếu đã có Model được nạp sẵn (Singleton), sử dụng nó để tiết kiệm RAM (V5.0 Optimization)
        if model_instance is not None:
            self.model = model_instance
            # Lấy thiết bị (V5.3.1 fix for compiled models)
            try:
                self.device = next(self.model.parameters()).device
            except (StopIteration, AttributeError):
                self.device = 'cpu'
            logger.info(f">>> AI Engine tái sử dụng Model dùng chung trên {self.device}")
        else:
            final_model = model_path if model_path and os.path.exists(model_path) else "models/yolov8s.onnx"
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            try:
                self.model = YOLO(final_model, task="detect")
                logger.info(f">>> AI Engine khởi tạo Model mới: {final_model} trên {self.device}")
            except Exception as e:
                logger.error(f"Lỗi khởi tạo AI: {e}")
                # Fallback an toàn (V5.4 Cleanup)
                if os.path.exists("models/yolov8s.onnx"):
                    self.model = YOLO("models/yolov8s.onnx")
                else:
                    logger.critical("KHÔNG TÌM THẤY MÔ HÌNH AI NÀO ĐỂ CHẠY!")

        self.conf = 0.15
        self.config_path = config_path
        self.last_config_mtime = 0
        self.last_config_check = 0
        self.roi_polygon = None
        self.roi_mask = None
        self.current_roi = None
        
        # BỘ NHỚ TRÍ NHỚ TẠM (Chống nháy Bounding Box)
        # Giúp ghi nhớ vị trí trong 5 frame tiếp theo nếu AI bị mất dấu đột ngột
        self.memory = {} # {id: {"box": [x1,y1,x2,y2], "safe": bool, "frames": int}}
        self.max_memory_frames = 5
        
        self.load_config()

    def load_config(self):
        """Tải cấu hình ROI từ file JSON"""
        if os.path.exists(self.config_path):
            try:
                self.last_config_mtime = os.path.getmtime(self.config_path)
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    pts = config.get("roi_points") or config.get("roi_polygon") or []
                    self.roi_polygon = np.array(pts, dtype=np.int32)
                    if len(self.roi_polygon) > 0:
                        self.current_roi = self.roi_polygon.copy()
                self.roi_mask = None
                logger.info(f"Đã tải/Cập nhật ROI từ {self.config_path}")
            except Exception as e:
                logger.error(f"Lỗi tải ROI config: {e}")

    def detect_people(self, frame):
        # Chỉ kiểm tra file cấu hình mỗi 2 giây để tránh lag Disk I/O
        now = time.time()
        if now - self.last_config_check > 2.0:
            self.last_config_check = now
            if os.path.exists(self.config_path):
                mtime = os.path.getmtime(self.config_path)
                if mtime > self.last_config_mtime:
                    self.load_config()
                
        h, w = frame.shape[:2]
        if (self.roi_mask is None or self.roi_mask.shape != (h, w)) and self.roi_polygon is not None and len(self.roi_polygon) > 0:
            self.roi_mask = np.zeros((h, w), dtype=np.uint8)
            # Scale ROI chuẩn Web (640x360) sang kích thước thực tế Camera
            scale_x, scale_y = w / 640.0, h / 360.0
            scaled_poly = np.array([[int(p[0] * scale_x), int(p[1] * scale_y)] for p in self.roi_polygon], dtype=np.int32)
            cv2.fillPoly(self.roi_mask, [scaled_poly], 255)
            self.current_roi = scaled_poly

        # Sử dụng Tự động Tracking với imgsz=640 để tăng tốc độ xử lý
        results = self.model.track(frame, persist=True, classes=[0], conf=self.conf, 
                                  verbose=False, device=self.device, imgsz=640)
        current_detections = []
        found_ids = set()
        
        if results and results[0].boxes is not None:
            for r in results[0].boxes:
                box = r.xyxy[0].cpu().numpy().astype(int)
                # Lấy ID được cấp bởi YOLO Tracker (nếu có)
                track_id = int(r.id[0].item()) if r.id is not None else -1
                
                x1, y1, x2, y2 = box
                is_safe = False
                if self.roi_mask is not None:
                    # Cách đơn giản nhất: Kiểm tra xem bất kỳ phần nào của Bounding Box
                    # có chồng lấn (overlap) với vùng ROI hay không.
                    box_roi = self.roi_mask[y1:y2, x1:x2]
                    if np.any(box_roi == 255):
                        is_safe = True
                            
                detection = {"box": [int(x1), int(y1), int(x2), int(y2)], "is_safe": is_safe}
                current_detections.append(detection)
                
                # Cập nhật Trí nhớ (Memory) nếu có ID định danh
                if track_id != -1:
                    found_ids.add(track_id)
                    self.memory[track_id] = {"detection": detection, "frames": 0}

        # XỬ LÝ HÀNH VI "NHÁY" - TRUY XUẤT TRÍ NHỚ (PERSISTENCE)
        missing_ids = [tid for tid in self.memory if tid not in found_ids]
        for tid in missing_ids:
            self.memory[tid]["frames"] += 1
            if self.memory[tid]["frames"] <= self.max_memory_frames:
                # Vẫn giữ lại detection cũ nếu vắng mặt chưa quá lâu (Chống nháy)
                current_detections.append(self.memory[tid]["detection"])
            else:
                # Quá lâu không thấy thì mời "biến mất" khỏi trí nhớ
                del self.memory[tid]
            
        # CHỐNG ĐẾM TRÙNG (Additional NMS)
        final_detections = []
        current_detections.sort(key=lambda x: (x["box"][2]-x["box"][0]) * (x["box"][3]-x["box"][1]), reverse=True)
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
                # Nếu chồng lấn trên 50% diện diện tích box nhỏ nằm nằm trong box lớn
                return True
        return False
