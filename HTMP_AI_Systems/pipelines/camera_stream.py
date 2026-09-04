"""
pipelines/camera_stream.py — Thread đọc liên tục từ RTSP camera

Chuyển từ: src/core/camera_stream.py
Thay đổi: Không có thay đổi logic, chỉ di chuyển vị trí
"""
import cv2
import threading
import time
import logging
import os

logger = logging.getLogger("Camera")


class CameraStreamer:
    def __init__(self, url):
        # Tự động ép kiểu sang int nếu url chỉ chứa các chữ số (ví dụ: "0", "1" của USB camera)
        try:
            if isinstance(url, str) and url.strip().isdigit():
                self.url = int(url.strip())
            else:
                self.url = url
        except Exception:
            self.url = url

        self.cap = None
        self.frame = None
        self.ret = False
        self.running = False
        self.frame_id = 0 # Đánh dấu ID khung hình (V5.6 Fix)
        self.lock = threading.Lock()


    def start(self):
        self.running = True
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        res_logged = False
        while self.running:
            loop_start = time.perf_counter()
            if self.cap is None or not self.cap.isOpened():
                # Tự động chọn backend dựa trên loại camera (USB hoặc RTSP/Video File)
                if isinstance(self.url, int):
                    # Trên Windows, CAP_DSHOW giúp khởi động và kiểm soát USB camera nhanh hơn nhiều
                    self.cap = cv2.VideoCapture(self.url, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
                else:
                    self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
                
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Giảm buffer xuống tối thiểu để tránh lag
                    with self.lock:
                        self.ret = True
                    logger.info(f"✅ Đã kết nối thành công tới Camera: {self.url}")
                else:
                    logger.error(f"❌ Không thể kết nối tới Camera: {self.url}. Thử lại sau 5s...")
                    with self.lock:
                        self.ret = False
                        self.frame = None
                    time.sleep(5)
                    continue

            try:
                ret, frame = self.cap.read()
            except Exception as e:
                logger.error(f"💥 Lỗi nghiêm trọng khi đọc từ camera: {e}")
                ret, frame = False, None
            
            if not ret or frame is None:
                logger.warning(f"⚠️ Mất kết nối hoặc lỗi khung hình từ camera: {self.url}. Đang giải phóng và thử kết nối lại...")
                with self.lock:
                    self.ret = False
                    self.frame = None
                
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                    self.cap = None
                
                time.sleep(2.0) # Đợi 2 giây trước khi thử kết nối lại
                continue

            # In độ phân giải ngay tại đây
            if not res_logged:
                h, w = frame.shape[:2]
                logger.info(f"📊 [CAMERA INFO] Độ phân giải thực tế: {w}x{h} | URL: {self.url}")
                res_logged = True
            
            # --- GUARD TỐI THƯỢNG: BẢO VỆ CPU KHỎI FFMPEG ---
            # Nếu ffmpeg bị lỗi h264 macroblock, nó có nguy cơ ném khung hình rác 
            # với tốc độ hàng nghìn khung/giây => nuốt 900% CPU.
            # Ta ép luồng đọc (StreamPuller) CHỈ được chạy tối đa 30/60 vòng mỗi giây.
            loop_duration = time.perf_counter() - loop_start
            if loop_duration < 0.033:  # Nhanh hơn 30 FPS (1/30 = 0.033s)
                time.sleep(0.033 - loop_duration)

            with self.lock:
                self.ret = ret
                if ret:
                    self.frame = frame
                    self.frame_id += 1

    def read(self, copy=True):
        """Trả về ret, frame, frame_id. Nếu copy=False, trả về reference (Tiết kiệm CPU)"""
        with self.lock:
            if not self.ret or self.frame is None:
                return False, None, self.frame_id
            
            frame = self.frame.copy() if copy else self.frame
            return True, frame, self.frame_id

    def stop(self):
        self.running = False
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
