import logging
from ultralytics import YOLO
from src.services.ai_worker import AIWorker

logger = logging.getLogger("WorkerManager")

class WorkerManager:
    def __init__(self, db_manager, socketio):
        self.db_manager = db_manager
        self.socketio = socketio
        self.active_workers = {} # {camera_id: AIWorkerInstance}
        self.shared_model = None

    def start_workers(self, model_path, alarm_delay):
        """Khởi động AI cho tất cả camera đang hoạt động trong DB"""
        cameras = self.db_manager.get_cameras(active_only=True)
        if not cameras:
            logger.warning("Không tìm thấy camera nào trong Database để khởi động.")
            return

        # Nạp mô hình DUY NHẤT một lần để tiết kiệm RAM (V5.0 Optimization)
        if self.shared_model is None:
            logger.info(f"Đang nạp mô hình dùng chung từ: {model_path}")
            self.shared_model = YOLO(model_path)

        for cam in cameras:
            cam_id = cam['id']
            if cam_id not in self.active_workers:
                worker = AIWorker(
                    camera_id=cam_id,
                    name=cam['name'],
                    rtsp_url=cam['url'],
                    model_instance=self.shared_model,
                    config_path=f"data/roi_config_{cam_id}.json",
                    alarm_delay=alarm_delay,
                    db_manager=self.db_manager,
                    socketio=self.socketio
                )
                worker.start()
                self.active_workers[cam_id] = worker
                logger.info(f"Đã khởi động Worker cho Camera ID {cam_id}: {cam['name']}")

    def stop_all(self):
        """Dừng toàn bộ các worker"""
        for cam_id, worker in self.active_workers.items():
            worker.stop()
            logger.info(f"Đã dừng Worker cho Camera ID {cam_id}")
        self.active_workers = {}

