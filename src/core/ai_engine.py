import cv2
import numpy as np
import json
import os
from ultralytics import YOLO

class AIEngine:
    def __init__(self, model_path="yolov8s.pt", config_path="roi_config.json"):
        # Load model YOLOv8 (phiên bản Small chuyên dụng cho công nghiệp)
        self.model = YOLO(model_path)
        self.conf = float(os.getenv("CONFIDENCE_THRESHOLD", 0.4))
        self.config_path = config_path
        self.roi_polygon = None
        self.roi_mask = None # Mặt nạ đa giác để kiểm tra giao cắt
        self.load_config()

    def load_config(self):
        """Tải cấu hình ROI từ file JSON và tạo mặt nạ (mask)"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                self.roi_polygon = np.array(config["roi_polygon"], dtype=np.int32)
                res_w, res_h = config["original_resolution"]
                
                # Tạo mặt nạ đa giác ngay lập tức
                self.roi_mask = np.zeros((res_h, res_w), dtype=np.uint8)
                cv2.fillPoly(self.roi_mask, [self.roi_polygon], 255)
                    
                print(f"AIEngine: Đã tải ROI và tạo Mask {res_w}x{res_h} từ {self.config_path}")
        else:
            print(f"AIEngine: Không tìm thấy file cấu hình {self.config_path}")

    def reload_roi(self, new_points):
        """Cập nhật ROI mới từ web và lưu lại file json"""
        try:
            self.roi_polygon = np.array(new_points, dtype=np.int32)
            # Cập nhật mask dựa trên độ phân giải hiện tại của mask (hoặc từ config)
            if self.roi_mask is not None:
                h, w = self.roi_mask.shape
                self.roi_mask = np.zeros((h, w), dtype=np.uint8)
                cv2.fillPoly(self.roi_mask, [self.roi_polygon], 255)
            
            # Lưu vào file JSON
            with open(self.config_path, "r") as f:
                config = json.load(f)
            config["roi_polygon"] = new_points
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
            
            print("AIEngine: Đã cập nhật ROI mới thành công!")
            return True
        except Exception as e:
            print(f"AIEngine Error: Không thể cập nhật ROI: {e}")
            return False

    def detect_people(self, frame):
        """
        Nhận diện người trong frame.
        Trả về danh sách các dict chứa thông tin detection.
        """
        # Chạy inference với mô hình thông minh hơn
        # imgsz=640 đảm bảo nhìn rõ chi tiết, iou=0.45 giúp tách biệt 2 người đứng sát nhau
        results = self.model.predict(frame, classes=[0], conf=self.conf, iou=0.45, imgsz=640, verbose=False)
        
        detections = []
        if not results:
            return detections

        h, w = frame.shape[:2]
        
        # Tự động tạo lại Mask nếu độ phân giải camera thay đổi
        if self.roi_mask is None or self.roi_mask.shape != (h, w):
            self.roi_mask = np.zeros((h, w), dtype=np.uint8)
            if self.roi_polygon is not None:
                cv2.fillPoly(self.roi_mask, [self.roi_polygon], 255)

        for r in results[0].boxes:
            box = r.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = box
            
            # Clip tọa độ để tránh lỗi index
            x1, x2 = np.clip([x1, x2], 0, w - 1)
            y1, y2 = np.clip([y1, y2], 0, h - 1)
            
            # LOGIC QUAN TRỌNG: Chỉ kiểm tra "Điểm chân" (Foot-point)
            # foot_x = chính giữa chiều ngang, foot_y = mép dưới cùng của khung
            foot_x = int((x1 + x2) / 2)
            foot_y = y2
            
            is_safe = False
            if self.roi_mask is not None:
                # Kiểm tra xem "Điểm chân" có nằm trong vùng 255 của Mask không
                if self.roi_mask[foot_y, foot_x] == 255:
                    is_safe = True
            
            detections.append({
                "box": [x1, y1, x2, y2],
                "is_safe": is_safe,
                "conf": float(r.conf[0])
            })
            
        return detections

if __name__ == "__main__":
    # Test nhanh engine với ảnh trắng
    engine = AIEngine()
    dummy_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    results = engine.detect_people(dummy_frame)
    print(f"Đã detect {len(results)} người trên frame mẫu.")
