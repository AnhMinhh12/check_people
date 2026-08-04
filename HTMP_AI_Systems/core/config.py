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

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings:
    """Singleton class chứa toàn bộ cấu hình hệ thống, đọc từ .env"""

    # --- Server ---
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")

    # --- AI Model ---
    _env_model = os.getenv("MODEL_PATH", "models/yolov8s.onnx")
    MODEL_PATH: str = os.path.normpath(_env_model if os.path.isabs(_env_model) else os.path.join(PROJECT_ROOT, _env_model))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", 0.1))
    ALARM_DELAY_SECONDS: float = float(os.getenv("ALARM_DELAY_SECONDS", 10.0))
    AI_MAX_FPS: float = float(os.getenv("AI_MAX_FPS", 15.0))

    # --- Database (Enterprise Standard) ---
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME", "aisystem")

    # Tự động tạo URL kết nối từ các biến lẻ hoặc sử dụng DATABASE_URL nếu có
    @property
    def DATABASE_URL(self) -> str:
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        
        # Nếu đầy đủ thông tin MySQL thì tạo MySQL URL, ngược lại dùng SQLite mặc định
        if all([self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME]):
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
        sqlite_path = os.path.join(PROJECT_ROOT, "../data/sentinel.db")
        return f"sqlite:///{os.path.normpath(sqlite_path)}"


    PROJECT_ROOT: str = PROJECT_ROOT
    
    # --- Data Storage ---
    _env_data = os.getenv("DATA_DIR", "../data")
    DATA_DIR: str = os.path.normpath(_env_data if os.path.isabs(_env_data) else os.path.join(PROJECT_ROOT, _env_data))

    _env_vio = os.getenv("VIOLATIONS_DIR", "violations")
    VIOLATIONS_DIR: str = os.path.normpath(_env_vio if os.path.isabs(_env_vio) else os.path.join(PROJECT_ROOT, _env_vio))
    
    _env_log = os.getenv("LOGS_DIR", "logs")
    LOGS_DIR: str = os.path.normpath(_env_log if os.path.isabs(_env_log) else os.path.join(PROJECT_ROOT, _env_log))

    # --- Camera Discovery ---
    MAX_CAMERAS: int = int(os.getenv("MAX_CAMERAS", 100))

    # --- Gmail SMTP Notifications ---
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    NOTIFICATION_EMAILS: str = os.getenv("NOTIFICATION_EMAILS", "") # Danh sách email ngăn cách bởi dấu phẩy

    @property
    def recipient_list(self) -> list:
        if not self.NOTIFICATION_EMAILS:
            return []
        return [email.strip() for email in self.NOTIFICATION_EMAILS.split(",") if email.strip()]

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
