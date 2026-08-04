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


import re
import unicodedata

def slugify(value):
    """
    Chuyển đổi tên có dấu/khoảng trắng thành dạng slug an toàn cho filename Windows
    """
    value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '_', value)

def get_camera_logger(camera_id: int, camera_name: str = "") -> logging.Logger:
    """Tạo logger riêng cho từng camera, ghi vào file logs/camera_{id}_{name}.log"""
    logs_dir = settings.LOGS_DIR
    os.makedirs(logs_dir, exist_ok=True)

    # Tạo tên file an toàn
    safe_name = slugify(camera_name)
    log_filename = f"camera_{camera_id}_{safe_name}.log" if safe_name else f"camera_{camera_id}.log"

    logger = logging.getLogger(f"AIWorker_CAM_{camera_id}")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        fh = logging.FileHandler(
            os.path.join(logs_dir, log_filename),
            encoding="utf-8"
        )
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)
        logger.propagate = False 

    return logger
