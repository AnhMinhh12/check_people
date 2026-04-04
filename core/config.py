"""
core/config.py — Quản lý tập trung tất cả biến môi trường (.env)

Sử dụng:
    from core.config import settings
    print(settings.MODEL_PATH)
"""
import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env (nếu tồn tại)
load_dotenv()


class Settings:
    """Singleton class chứa toàn bộ cấu hình hệ thống, đọc từ .env"""

    # --- Server ---
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")

    # --- AI Model ---
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/yolov8s.onnx")
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", 0.15))
    ALARM_DELAY_SECONDS: float = float(os.getenv("ALARM_DELAY_SECONDS", 5.0))
    AI_MAX_FPS: float = float(os.getenv("AI_MAX_FPS", 10.0))

    # --- Database ---
    # SQLite (Dev):  sqlite:///data/sentinel.db
    # MySQL (Prod):  mysql+pymysql://user:pass@host:3306/sentinel_db
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/sentinel.db")

    # --- Data Storage ---
    VIOLATIONS_DIR: str = os.getenv("VIOLATIONS_DIR", "data/violations")
    LOGS_DIR: str = os.getenv("LOGS_DIR", "logs")

    # --- Camera Discovery ---
    MAX_CAMERAS: int = int(os.getenv("MAX_CAMERAS", 100))

    @classmethod
    def get_camera_configs(cls) -> list:
        """Quét biến môi trường để tìm tất cả cấu hình camera (RTSP_URL{i}, CAMERA_NAME{i})"""
        camera_configs = []

        # 1. Camera mặc định (RTSP_URL không số)
        default_rtsp = os.getenv("RTSP_URL")
        if default_rtsp:
            camera_configs.append(("Camera Mặc Định", default_rtsp))

        # 2. Camera đánh số (RTSP_URL1, RTSP_URL2, ...)
        for i in range(1, cls.MAX_CAMERAS + 1):
            url = os.getenv(f"RTSP_URL{i}")
            if url:
                name = os.getenv(f"CAMERA_NAME{i}", f"Camera {i}")
                camera_configs.append((name, url))

        return camera_configs


# Singleton instance — import trực tiếp để sử dụng
settings = Settings()
