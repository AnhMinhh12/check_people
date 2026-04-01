import cv2
import numpy as np
import json
import os
import logging
from ultralytics import YOLO

logger = logging.getLogger("AIEngine")

class AIEngine:
    def __init__(self, model_path="models/yolov8s.pt", config_path="roi_config.json"):
        # Ưu tiên các model có sẵn trong máy
        final_model = model_path if os.path.exists(model_path) else "yolov8n.pt"
        self.model = YOLO(final_model)
        self.conf = 0.25
        self.config_path = config_path
        self.roi_polygon = None
        self.roi_mask = None
        self.current_roi = None
        self.load_config()

    def load_config(self):
        """Tải cấu hình ROI từ file JSON"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    # Chấp nhận cả roi_points (web mới) và roi_polygon (cũ)
                    pts = config.get("roi_points") or config.get("roi_polygon") or []
                    self.roi_polygon = np.array(pts, dtype=np.int32)
                    if len(self.roi_polygon) > 0:
                        self.current_roi = self.roi_polygon.copy()
                logger.info(f"Đã tải thành công ROI từ {self.config_path}")
            except Exception as e:
                logger.error(f"Lỗi tải ROI config: {e}")

    def detect_people(self, frame):
        h, w = frame.shape[:2]
        
        # Tự động cập nhật Mask nếu Camera thay đổi độ phân giải
        if (self.roi_mask is None or self.roi_mask.shape != (h, w)) and self.roi_polygon is not None and len(self.roi_polygon) > 0:
            self.roi_mask = np.zeros((h, w), dtype=np.uint8)
            # Dashboard scale chuẩn 640x360
            scale_x, scale_y = w / 640.0, h / 360.0
            scaled_poly = np.array([[int(p[0] * scale_x), int(p[1] * scale_y)] for p in self.roi_polygon], dtype=np.int32)
            cv2.fillPoly(self.roi_mask, [scaled_poly], 255)
            self.current_roi = scaled_poly

        results = self.model.predict(frame, classes=[0], conf=self.conf, verbose=False)
        detections = []
        
        for r in results[0].boxes:
            box = r.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = box
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            fx, fy = cx, min(y2, h - 1)
            
            is_safe = False
            if self.roi_mask is not None:
                # 1. Ưu tiên kiểm tra điểm chân (Chính xác cao nhất)
                if self.roi_mask[fy, fx] == 255:
                    is_safe = True
                # 2. Dự phòng: Nếu chân không ở trong (có thể bị che bởi biển/thùng), kiểm tra tâm người
                elif self.roi_mask[cy, cx] == 255:
                    is_safe = True
            
            detections.append({"box": [int(x1), int(y1), int(x2), int(y2)], "is_safe": is_safe})
            
        return detections
