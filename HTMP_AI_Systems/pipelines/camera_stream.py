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
                # Tối ưu hóa FFMPEG mạnh tay để giảm lỗi 'error while decoding MB'
                # threads=1 giúp giảm tải CPU giải mã cực lớn
                self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Giảm buffer xuống tối thiểu để tránh lag
                    self.ret = True
                    logger.info(f"✅ Đã kết nối thành công tới Camera: {self.url}")
                else:
                    logger.error(f"❌ Không thể kết nối tới Camera: {self.url}. Thử lại sau 5s...")
                    time.sleep(5)
                    continue

            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                # Nếu lỗi giải mã, không nên log quá nhiều gây treo console
                # Chỉ log cảnh báo mỗi 5 giây một lần
                time.sleep(0.1)
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
            self.cap.release()
