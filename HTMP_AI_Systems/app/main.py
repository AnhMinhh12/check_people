"""
app/main.py — Entry Point: Khởi tạo Flask, SocketIO, đồng bộ Camera, chạy AI Workers

Kiến trúc HTMP_AI_Systems:
  - Cấu hình tập trung qua core.config.settings
  - Database: SQLAlchemy + Repository Pattern (db/)
  - Logging tập trung qua core.logging.setup_logging
"""
import os
import sys
import io

# Fix UnicodeEncodeError on Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for Python < 3.7
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- TỐI ƯU HÓA CPU CHO SERVER RAM LỚN (CHỐNG 100% CPU TRÊN 250GB RAM) ---
# ONNX/PyTorch mặc định sẽ tạo [Số nhân CPU] luồng cho MỖI camera. 
# Nếu server có 128 nhân và 10 camera = 1280 luồng -> NGẼN CPU VÀ SẬP CHƯƠNG TRÌNH!
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
# --- CHẶN ĐỨNG HÀNH VI "SPIN WAIT" GÂY 38 TRIỆU CONTEXT SWITCH CỦA C++ ---
os.environ["OMP_WAIT_POLICY"] = "PASSIVE"
os.environ["KMP_BLOCKTIME"] = "0"
os.environ["MKL_DYNAMIC"] = "FALSE"

# --- TỐI ƯU MẠNG YẾU (CHỐNG SPAM H264 MACROBLOCK ERROR) ---
# rtsp_transport;tcp: Ép dùng TCP chống rớt gói
# fflags;discardcorrupt: Vứt bỏ khung hình hỏng (BỎ CHỮ 'nobuffer' đi để tránh FFMPEG spin-loop 1 vạn vòng/s)
# probesize;32: Giảm kích thước phân tích gói tin ban đầu
# threads;1: ÉP FFMPEG CHỈ DÙNG 1 LUỒNG GIẢI MÃ VIDEO
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|fflags;discardcorrupt|probesize;32|threads;1" 
os.environ["OPENCV_LOG_LEVEL"] = "FATAL" # Chỉ hiện lỗi cực nghiêm trọng
os.environ["OPENCV_FFMPEG_DEBUG"] = "0"

import cv2
cv2.setNumThreads(0) # Tắt hoàn toàn Thread Pool của OpenCV (Cận chiến 1 luồng)

import sys
import torch
torch.set_num_threads(1) # Giới hạn luồng của PyTorch/YOLO

# --- HACK MẠNH TAY: ÉP ONNX RUNTIME CHỈ DÙNG 1 LUỒNG ---
try:
    import onnxruntime as ort
    
    def apply_ort_optimization(session_class):
        _original_init = session_class.__init__
        def _patched_init(self, path_or_bytes, sess_options=None, providers=None, provider_options=None, **kwargs):
            if sess_options is None:
                sess_options = ort.SessionOptions()
            # ÉP CỨNG: Mỗi model AI chỉ được dùng tối đa 2 luồng (phù hợp với Server nhiều nhân)
            sess_options.intra_op_num_threads = 2
            sess_options.inter_op_num_threads = 1
            sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # --- ĐIỂM CHẾT: TẮT TÍNH NĂNG "CỐ QUAY ĐỂ ĐỢI" CỦA C++ EIGEN THREADPOOL ---
            if hasattr(sess_options, 'add_session_config_entry'):
                sess_options.add_session_config_entry("session.intra_op.allow_spinning", "0")
                sess_options.add_session_config_entry("session.inter_op.allow_spinning", "0")
                
            return _original_init(self, path_or_bytes, sess_options, providers, provider_options, **kwargs)
        session_class.__init__ = _patched_init

    # Patch cả class chính và class trong capi (nơi Ultralytics có thể gọi)
    apply_ort_optimization(ort.InferenceSession)
    try:
        from onnxruntime.capi.onnxruntime_inference_collection import InferenceSession as InferenceSessionInternal
        apply_ort_optimization(InferenceSessionInternal)
    except: pass
    
    print(">>> [HỆ THỐNG] Đã khóa số luồng AI (Max 2 thread/model) để bảo vệ CPU.")
except ImportError:
    pass

from flask import Flask, render_template
from flask_socketio import SocketIO
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # Đảm bảo log được in ra ngay lập tức

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config import settings
from core.logging import setup_logging
from db.connection import init_db
from db.repository import CameraRepository, ZoneRepository, EventRepository, SystemHealthRepository
from pipelines.worker_manager import WorkerManager
from app.routes import api_bp

# Khởi tạo Logging tập trung
setup_logging()

# Khởi tạo Database (tạo tables nếu chưa có)
init_db()

# Khởi tạo Flask — template_folder trỏ lên thư mục templates/ ở gốc dự án
app = Flask(__name__, template_folder=os.path.join(PROJECT_ROOT, 'templates'))
# Fix lỗi "Invalid frame header": Tăng buffer lên 10MB và nới lỏng ping timeout để chống đứt kết nối WebSocket khi stream ảnh lớn
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', max_http_buffer_size=1e7, ping_timeout=60, ping_interval=25)
app.register_blueprint(api_bp)

# Repositories (Repository Pattern)
cam_repo = CameraRepository()
event_repo = EventRepository()
zone_repo = ZoneRepository()
health_repo = SystemHealthRepository()

# --- ĐỒNG BỘ CAMERA TỪ .ENV ---
camera_configs = settings.get_camera_configs()
for name, url in camera_configs:
    cam_repo.sync(name, url)

# DỌN DẸP: Xóa các camera không còn trong file .env
camera_configs = settings.get_camera_configs()
if camera_configs:
    cam_repo.delete_orphaned(camera_configs)

# --- TỰ ĐỘNG ĐỒNG BỘ VÙNG ROI TỪ FILE VÀO DB (CHỐNG LỆCH DỮ LIỆU) ---
import json
for cam in cam_repo.get_all(active_only=False):
    cam_id = cam['id']
    json_path = os.path.join(PROJECT_ROOT, f"../data/roi_config_{cam_id}.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                zones_data = config.get('roi_zones', [])
                if zones_data:
                    zone_repo.update_camera_zones(cam_id, zones_data)
        except: pass

# Khởi tạo Worker Manager
manager = WorkerManager(event_repo, cam_repo, zone_repo, socketio)


@app.route('/')
def index():
    cameras = cam_repo.get_all()
    zones = zone_repo.get_all_active()
    return render_template('index.html', cameras=cameras, zones=zones)


@socketio.on('focus_camera')
def handle_focus(data):
    """Lắng nghe yêu cầu xem camera cụ thể từ Web"""
    cam_id = data.get('camera_id')
    if cam_id:
        manager.set_focus_camera(int(cam_id))


@socketio.on('view_all_cameras')
def handle_view_all(data):
    """Bật/tắt chế độ Live Grid: xem tất cả camera cùng lúc"""
    enabled = data.get('enabled', False)
    manager.set_all_cameras_focused(enabled)


if __name__ == '__main__':
    try:
        # Khởi động AI cho tất cả camera
        manager.start_workers(settings.MODEL_PATH, settings.ALARM_DELAY_SECONDS, settings.AI_MAX_FPS)

        # --- BỘ THEO DÕI TÀI NGUYÊN (PROFILER) ĐỂ DEBUG 100% CPU ---
        def resource_monitor():
            import psutil
            import time
            import logging
            logger = logging.getLogger("SystemMonitor")
            process = psutil.Process(os.getpid())
            # Khởi động bộ đo CPU
            process.cpu_percent(interval=None)
            
            while True:
                time.sleep(10) # Báo cáo tốc độ 10s / lần
                try:
                    # CPU Toàn hệ thống (0-100%)
                    global_cpu = psutil.cpu_percent(interval=None)
                    # CPU của riêng tiến trình này (Cộng dồn các nhân)
                    process_cpu = process.cpu_percent(interval=None)

                    mem = process.memory_info().rss / (1024 * 1024)
                    threads = process.num_threads()
                    # Phân tích luồng bận (Context Switches) để tìm vòng lặp vô tận (nếu có)
                    ctx = process.num_ctx_switches()
                    # Cập nhật sức khỏe vào DB
                    health_repo.update(node_name="Primary-Server", gpu_load=0, fps=0.0)
                    
                    logger.info(f"📊 [KIỂM TRA TẢI] TỔNG CPU SERVER: {global_cpu}% | CPU App AI: {process_cpu:.1f}% | RAM: {mem:.1f} MB | Threads: {threads}")
                except: pass

        import threading
        monitor_thread = threading.Thread(target=resource_monitor, daemon=True)
        monitor_thread.start()

        print(f"\n>>> WARDEN ENTERPRISE SERVER READY AT http://{settings.FLASK_HOST}:{settings.FLASK_PORT}\n")
        socketio.run(app, host=settings.FLASK_HOST, port=settings.FLASK_PORT,
                    debug=settings.FLASK_DEBUG, allow_unsafe_werkzeug=True)
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger("SystemExit")
        logger.critical(f"CHƯƠNG TRÌNH SẬP DO LỖI NGHIÊM TRỌNG:\n{traceback.format_exc()}")
        os._exit(1)
