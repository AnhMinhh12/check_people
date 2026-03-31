import os
import logging
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Import các thành phần đã tách
from src.database.db_manager import DBManager
from src.services.ai_worker import AIWorker
from src.api.routes import create_api_blueprint

# Load environment variables
load_dotenv()

# Cấu hình log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WardenApp")

# Đường dẫn & Cấu hình
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIOLATIONS_DIR = os.path.join(BASE_DIR, "violations")
DB_PATH = os.path.join(BASE_DIR, "sentinel.db")
VIOLATIONS_FILE_OLD = os.path.join(BASE_DIR, "violations.json")

# RTSP & Mode Settings từ .env
RTSP_URL = os.getenv("RTSP_URL")
MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")
ALARM_DELAY_SECONDS = float(os.getenv("ALARM_DELAY_SECONDS", 5.0))
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

def create_app():
    # 1. Khởi tạo Flask & SocketIO
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', allow_upgrades=False)

    # 2. Khởi tạo Database Manager
    db_manager = DBManager(DB_PATH, VIOLATIONS_DIR, VIOLATIONS_FILE_OLD)

    # 3. Khởi tạo AI Worker (Background Service)
    ai_worker = AIWorker(
        rtsp_url=RTSP_URL,
        model_path=MODEL_PATH,
        config_path="roi_config.json",
        alarm_delay=ALARM_DELAY_SECONDS,
        db_manager=db_manager,
        socketio=socketio
    )
    ai_worker.daemon = True
    ai_worker.start()

    # 4. Đăng ký API Routes (Blueprints)
    api_bp = create_api_blueprint(ai_worker, db_manager, VIOLATIONS_DIR)
    app.register_blueprint(api_bp)

    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    logger.info(f">>> WARDEN SERVER READY AT http://localhost:{FLASK_PORT}")
    socketio.run(app, host='0.0.0.0', port=FLASK_PORT, debug=FLASK_DEBUG, use_reloader=False, allow_unsafe_werkzeug=True)
