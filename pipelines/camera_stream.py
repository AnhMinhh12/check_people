"""
pipelines/camera_stream.py — Thread đọc liên tục từ RTSP camera

Chuyển từ: src/core/camera_stream.py
Thay đổi: Không có thay đổi logic, chỉ di chuyển vị trí
"""
import cv2
import threading
import time
import logging

logger = logging.getLogger("Camera")


class CameraStreamer:
    def __init__(self, url):
        self.url = url
        self.cap = None
        self.frame = None
        self.ret = False
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        self.running = True
        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.url)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.ret = True
                else:
                    time.sleep(2)
                    continue

            ret, frame = self.cap.read()
            with self.lock:
                self.ret = ret
                if ret:
                    self.frame = frame
            if not ret:
                time.sleep(0.1)

    def read(self):
        with self.lock:
            return self.ret, (self.frame.copy() if self.frame is not None else None), 0

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
