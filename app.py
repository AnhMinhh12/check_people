import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_socketio import SocketIO
from src.core.database import DatabaseManager
from src.core.worker_manager import WorkerManager
from src.api.routes import api_bp

# Load cấu hình từ file .env
load_dotenv()

# Tinh giản Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)
# Dùng threading để tương thích tốt với OpenCV trên Windows
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
app.register_blueprint(api_bp)

# Cấu hình từ Biến môi trường (.env)
MODEL_PATH = os.getenv("MODEL_PATH", "models/yolov8n.pt")
ALARM_DELAY = float(os.getenv("ALARM_DELAY_SECONDS", 5.0))
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
AI_MAX_FPS = float(os.getenv("AI_MAX_FPS", 10.0))


db_manager = DatabaseManager()

# --- ĐỒNG BỘ CAMERA TỪ .ENV ---
# Tìm tất cả RTSP_URL, RTSP_URL1, RTSP_URL2...
camera_configs = []
# 1. Kiểm tra RTSP_URL mặc định
default_rtsp = os.getenv("RTSP_URL")
if default_rtsp:
    camera_configs.append(("Camera Mặc Định", default_rtsp))

# 2. Quét các camera đánh số (RTSP_URL1, RTSP_URL2...)
for i in range(1, 101): # Hỗ trợ tối đa 100 camera từ env
    url = os.getenv(f"RTSP_URL{i}")
    if url:
        name = os.getenv(f"CAMERA_NAME{i}", f"Camera {i}")
        camera_configs.append((name, url))

# 3. Thực hiện đồng bộ vào DB
for name, url in camera_configs:
    db_manager.sync_camera(name, url, "Zone A")

# 4. DỌN DẸP: Xóa các camera không còn trong file .env
active_urls = [cfg[1] for cfg in camera_configs]
if active_urls:
    db_manager.delete_orphaned_cameras(active_urls)

manager = WorkerManager(db_manager, socketio)

@app.route('/')
def index():
    cameras = db_manager.get_cameras()
    return render_template('index.html', cameras=cameras)

if __name__ == '__main__':
    # Khởi động AI cho tất cả camera
    manager.start_workers(MODEL_PATH, ALARM_DELAY, AI_MAX_FPS)
    
    print(f"\n>>> WARDEN ENTERPRISE SERVER READY AT http://{FLASK_HOST}:{FLASK_PORT}\n")
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, allow_unsafe_werkzeug=True)
