"""
app/main.py — Entry Point: Khởi tạo Flask, SocketIO, đồng bộ Camera, chạy AI Workers

Kiến trúc HTMP_AI_Systems:
  - Cấu hình tập trung qua core.config.settings
  - Database: SQLAlchemy + Repository Pattern (db/)
  - Logging tập trung qua core.logging.setup_logging
"""
import os
from flask import Flask, render_template
from flask_socketio import SocketIO

from core.config import settings
from core.logging import setup_logging
from db.connection import init_db
from db.repository import CameraRepository, ViolationRepository
from pipelines.worker_manager import WorkerManager
from app.routes import api_bp

# Khởi tạo Logging tập trung
setup_logging()

# Khởi tạo Database (tạo tables nếu chưa có)
init_db()

# Khởi tạo Flask — template_folder trỏ lên thư mục templates/ ở gốc dự án
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
app.register_blueprint(api_bp)

# Repositories (Repository Pattern)
cam_repo = CameraRepository()
vio_repo = ViolationRepository()

# --- ĐỒNG BỘ CAMERA TỪ .ENV ---
camera_configs = settings.get_camera_configs()
for name, url in camera_configs:
    cam_repo.sync(name, url, "Zone A")

# DỌN DẸP: Xóa các camera không còn trong file .env
active_urls = [cfg[1] for cfg in camera_configs]
if active_urls:
    cam_repo.delete_orphaned(active_urls)

# Khởi tạo Worker Manager
manager = WorkerManager(vio_repo, cam_repo, socketio)


@app.route('/')
def index():
    cameras = cam_repo.get_all()
    return render_template('index.html', cameras=cameras)


if __name__ == '__main__':
    # Khởi động AI cho tất cả camera
    manager.start_workers(settings.MODEL_PATH, settings.ALARM_DELAY_SECONDS, settings.AI_MAX_FPS)

    print(f"\n>>> WARDEN ENTERPRISE SERVER READY AT http://{settings.FLASK_HOST}:{settings.FLASK_PORT}\n")
    socketio.run(app, host=settings.FLASK_HOST, port=settings.FLASK_PORT,
                 debug=settings.FLASK_DEBUG, allow_unsafe_werkzeug=True)
