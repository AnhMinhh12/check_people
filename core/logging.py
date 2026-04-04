"""
core/logging.py — Cấu hình logging tập trung cho toàn hệ thống

Sử dụng:
    from core.logging import setup_logging, get_camera_logger
"""
import os
import logging
from core.config import settings


def setup_logging(level=logging.INFO):
    """Thiết lập logging chung cho ứng dụng (gọi 1 lần lúc khởi động)"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Tinh giản log werkzeug (Flask internal)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)


def get_camera_logger(camera_id: int) -> logging.Logger:
    """Tạo logger riêng cho từng camera, ghi vào file logs/camera_{id}.log"""
    logs_dir = settings.LOGS_DIR
    os.makedirs(logs_dir, exist_ok=True)

    logger = logging.getLogger(f"AIWorker_CAM_{camera_id}")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fh = logging.FileHandler(
            os.path.join(logs_dir, f"camera_{camera_id}.log"),
            encoding="utf-8"
        )
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)
        logger.propagate = False  # Không tràn ra console chung

    return logger
