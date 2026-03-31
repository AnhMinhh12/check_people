import cv2
import threading
import time
import logging

# Cấu hình log để theo dõi trạng thái kết nối
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CameraStreamer:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.latest_frame = None
        self.ret = False
        self.running = False
        self.frame_id = 0 # Thêm ID để nhận diện frame mới
        self.thread = None
        
        # Thử kết nối lần đầu
        self._connect()

    def _connect(self):
        """Khởi tạo kết nối RTSP"""
        if self.cap is not None:
            self.cap.release()
            
        logging.info(f"Đang kết nối tới Camera: {self.rtsp_url}")
        # Sử dụng CAP_FFMPEG để tối ưu hóa luồng RTSP
        self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        
        # Tối ưu hóa buffer để giảm độ trễ (latency)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not self.cap.isOpened():
            logging.error("Không thể mở luồng RTSP. Vui lòng kiểm tra lại URL hoặc mạng.")
            return False
        
        logging.info("Kết nối thành công!")
        return True

    def start(self):
        """Bắt đầu luồng đọc frame trong background"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
        logging.info("Đã bắt đầu luồng đọc frame.")

    def _update(self):
        """Vòng lặp chạy trong thread riêng để cập nhật frame mới nhất"""
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                logging.warning("Mất kết nối. Đang thử kết nối lại sau 3 giây...")
                time.sleep(3)
                self._connect()
                continue

            ret, frame = self.cap.read()
            if ret:
                self.latest_frame = frame
                self.ret = True
                self.frame_id += 1 # Tăng ID mỗi khi có hình mới
            else:
                self.ret = False
                logging.warning("Không đọc được frame. Đang reload kết nối...")
                self._connect()
                time.sleep(1) # Tránh loop quá nhanh khi lỗi

    def read(self):
        """Trả về frame mới nhất, trạng thái và ID của nó"""
        return self.ret, self.latest_frame, self.frame_id

    def stop(self):
        """Dừng luồng và giải phóng tài nguyên"""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.cap:
            self.cap.release()
        logging.info("Đã dừng CameraStreamer.")

if __name__ == "__main__":
    # Test nhanh module
    URL = "rtsp://admin:Htmp%402019@192.168.103.14:554/Streaming/Channels/101"
    streamer = CameraStreamer(URL)
    streamer.start()

    try:
        while True:
            ret, frame = streamer.read()
            if ret and frame is not None:
                # Resize để hiển thị test (2K -> 720p)
                display_frame = cv2.resize(frame, (1280, 720))
                cv2.imshow("Camera 2K Test", display_frame)

            if cv2.waitKey(1) == 27: # Nhấn ESC để thoát
                break
    finally:
        streamer.stop()
        cv2.destroyAllWindows()
