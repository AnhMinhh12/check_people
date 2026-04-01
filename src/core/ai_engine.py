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

        results = self.model.track(frame, persist=True, classes=[0], conf=self.conf, verbose=False)
        detections = []
        
        if not results or not results[0].boxes:
            return []
            
        for r in results[0].boxes:
            box = r.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = box
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            fx, fy = cx, min(y2, h - 1)
            
            is_safe = False
            if self.roi_mask is not None:
                # Quét 3 mốc quan trọng ở nửa dưới cơ thể (75%, 90% và đáy 100%)
                # Điều này giúp nhận diện người đứng sau biển báo/vật cản nhưng loại bỏ việc "thò đầu/vai" vào vùng ROI.
                for ratio in [1.0, 0.9, 0.75]:
                    test_y = int(y1 + (y2 - y1) * ratio)
                    # Đảm bảo điểm kiểm tra nằm trong ảnh
                    test_y = max(0, min(test_y, h - 1))
                    
                    if self.roi_mask[test_y, cx] == 255:
                        is_safe = True
                        break # Chỉ cần 1 trong các điểm này chạm vùng xanh là OK
            
            detections.append({"box": [int(x1), int(y1), int(x2), int(y2)], "is_safe": is_safe})
            
        # CHỐNG ĐẾM TRÙNG (NMS Bổ sung): Lọc các box nằm đè lên nhau (do vật cản chia cắt cơ thể)
        final_detections = []
        # Sắp xếp từ box lớn đến box nhỏ để ưu tiên giữ box chính
        detections.sort(key=lambda x: (x["box"][2]-x["box"][0]) * (x["box"][3]-x["box"][1]), reverse=True)
        
        for d in detections:
            is_redundant = False
            for f in final_detections:
                if self._check_overlap(d["box"], f["box"]):
                    is_redundant = True
                    break
            if not is_redundant:
                final_detections.append(d)
                
        return final_detections

    def _check_overlap(self, box1, box2):
        """Kiểm tra nếu box1 nằm lọt trong hoặc chồng lấn mạnh với box2"""
        ax1, ay1, ax2, ay2 = box1
        bx1, by1, bx2, by2 = box2
        
        # Diện tích giao nhau
        inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
        inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
        
        if inter_x1 < inter_x2 and inter_y1 < inter_y2:
            inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
            area1 = (ax2 - ax1) * (ay2 - ay1)
            # Nếu > 50% diện tích box nhỏ nằm trong box lớn -> Coi là trùng
            if inter_area / float(area1) > 0.5:
                return True
        return False
