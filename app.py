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
RTSP_URL = os.getenv("RTSP_URL")
MODEL_PATH = os.getenv("MODEL_PATH", "models/yolov8n.pt")
ALARM_DELAY = float(os.getenv("ALARM_DELAY_SECONDS", 5.0))
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")

db_manager = DatabaseManager()

# Đảm bảo có ít nhất 1 camera trong DB để chạy test
if not db_manager.get_cameras():
    db_manager.add_camera("Camera Kho Chính", RTSP_URL, "Zone A")

manager = WorkerManager(db_manager, socketio)

@app.route('/')
def index():
    cameras = db_manager.get_cameras()
    return render_template('index.html', cameras=cameras)

if __name__ == '__main__':
    # Khởi động AI cho tất cả camera
    manager.start_workers(MODEL_PATH, ALARM_DELAY)
    
    print(f"\n>>> WARDEN ENTERPRISE SERVER READY AT http://{FLASK_HOST}:{FLASK_PORT}\n")
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, allow_unsafe_werkzeug=True)
