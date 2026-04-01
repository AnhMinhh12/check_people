import logging
from flask import Flask, render_template
from flask_socketio import SocketIO
from src.core.database import DatabaseManager
from src.services.ai_worker import AIWorker
from src.api.routes import api_bp

# Tinh giản Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
app.register_blueprint(api_bp)

# Cấu hình chuẩn
RTSP_URL = "rtsp://admin:Htmp%402019@192.168.103.14:554/Streaming/Channels/102"
MODEL_PATH = "models/yolov8n.pt"
CONFIG_PATH = "roi_config.json"
ALARM_DELAY = 5.0 # Giây

db_manager = DatabaseManager()
worker = AIWorker(RTSP_URL, MODEL_PATH, CONFIG_PATH, ALARM_DELAY, db_manager, socketio)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    worker.start()
    print(f"\n>>> WARDEN SERVER READY AT http://localhost:5000\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
