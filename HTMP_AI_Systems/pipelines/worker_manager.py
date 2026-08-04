"""
pipelines/worker_manager.py — Quản lý lifecycle của AI Workers cho tất cả camera

Kiến trúc HTMP_AI_Systems:
  - Nhận ViolationRepository + CameraRepository thay cho DatabaseManager
  - Truyền vio_repo xuống từng AIWorker
"""
import os
import logging
from ultralytics import YOLO
import numpy as np
from core.config import settings
from pipelines.ai_worker import AIWorker

logger = logging.getLogger("WorkerManager")


class WorkerManager:
    def __init__(self, event_repo, cam_repo, zone_repo, socketio):
        self.event_repo = event_repo
        self.cam_repo = cam_repo
        self.zone_repo = zone_repo
        self.socketio = socketio
        self.active_workers = {}  # {camera_id: AIWorkerInstance}
        self.shared_model_instance = None

    def start_workers(self, model_path, alarm_delay, ai_max_fps=10.0):
        """Khởi động AI cho tất cả camera đang hoạt động trong DB"""
        cameras = self.cam_repo.get_all(active_only=True)
        if not cameras:
            logger.warning("Không tìm thấy camera nào trong Database để khởi động.")
            return

        for cam in cameras:
            cam_id = cam['id']
            if cam_id not in self.active_workers:
                
                # --- SỬ DỤNG MÔ HÌNH DÙNG CHUNG THAY VÌ TẠO MỚI ---
                # Ngăn chặn YOLO/PyTorch tạo hàng chục background threads bằng cách tái sử dụng
                if self.shared_model_instance is None:
                    logger.info(f"🧬 Khởi tạo Model AI dùng chung để tiết kiệm CPU...")
                    self.shared_model_instance = YOLO(model_path, task="detect")
                    
                    # WARMUP model
                    dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
                    self.shared_model_instance.track(dummy_frame, verbose=False, imgsz=[360, 640])
                
                logger.info(f"Phân bổ Camera {cam_id} vào Shared Model.")

                worker = AIWorker(
                    camera_id=cam_id,
                    name=cam['name'],
                    rtsp_url=cam['url'],
                    model_instance=self.shared_model_instance,
                    config_path=os.path.join(settings.DATA_DIR, f"roi_config_{cam_id}.json"),
                    alarm_delay=alarm_delay,
                    ai_max_fps=ai_max_fps,
                    event_repo=self.event_repo,
                    zone_repo=self.zone_repo,
                    socketio=self.socketio
                )
                worker.daemon = True
                worker.start()
                self.active_workers[cam_id] = worker
                logger.info(f"✅ Đã khởi động Worker cho Camera ID {cam_id}: {cam['name']}")
                import time
                time.sleep(0.5)

    def set_focus_camera(self, camera_id):
        """Chỉ bật stream ảnh cho camera được chọn để tiết kiệm băng thông"""
        for cid, worker in self.active_workers.items():
            worker.is_focused = (cid == camera_id)
            worker.is_grid_mode = False  # Tắt grid mode khi focus 1 camera
        logger.info(f"🎯 Đã chuyển tiêu điểm (Focus) sang Camera ID: {camera_id}")

    def set_all_cameras_focused(self, enabled):
        """Bật/tắt chế độ Live Grid: stream ảnh chất lượng thấp cho TẤT CẢ camera"""
        for cid, worker in self.active_workers.items():
            worker.is_grid_mode = enabled
            worker.is_focused = enabled  # Bật stream ảnh cho tất cả
        logger.info(f"📺 Chế độ Live Grid: {'BẬT' if enabled else 'TẮT'} cho {len(self.active_workers)} camera")

    def reload_worker(self, camera_id):
        """Gửi lệnh nạp lại cấu hình cho một worker cụ thể"""
        worker = self.active_workers.get(camera_id)
        if worker:
            worker.reload_config()
            return True
        return False

    def stop_all(self):
        """Dừng toàn bộ các worker"""
        for cam_id, worker in self.active_workers.items():
            worker.stop()
            logger.info(f"Đã dừng Worker cho Camera ID {cam_id}")
        self.active_workers = {}
