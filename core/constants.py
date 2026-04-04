"""
core/constants.py — Hằng số hệ thống (không thay đổi theo môi trường)
"""

# Thông tin ứng dụng
APP_NAME = "Sentinel Warden AI"
APP_VERSION = "5.5"
APP_EDITION = "Enterprise"

# Trạng thái giám sát
STATUS_WAITING = "ĐANG CHỜ"
STATUS_SAFE = "AN TOÀN"
STATUS_LEFT = "RỜI VỊ TRÍ"
STATUS_VIOLATION = "VI PHẠM"

# AI Engine defaults
DEFAULT_PERSISTENCE_FRAMES = 5      # Số frame giữ vết khi mất dấu người (chống nháy)
DEFAULT_ROI_WEB_SIZE = (640, 360)    # Kích thước chuẩn ROI trên Web
DEFAULT_NMS_IOU_THRESHOLD = 0.5      # Ngưỡng IoU cho chống đếm trùng
DEFAULT_STATUS_BUFFER_SEC = 1.0      # Bộ đệm trạng thái (giây) trước khi chuyển AN TOÀN → RỜI VỊ TRÍ

# Dashboard
DASHBOARD_JPEG_QUALITY = 50          # Chất lượng JPEG gửi lên Dashboard
DASHBOARD_EMIT_FAST_HZ = 0.1        # Tần suất emit khi FPS cao (giây)
DASHBOARD_EMIT_SLOW_HZ = 0.2        # Tần suất emit khi FPS thấp (giây)
DASHBOARD_FPS_THRESHOLD = 10        # Ngưỡng FPS để chọn tốc độ emit

# Database
DB_TABLE_CAMERAS = "cameras"
DB_TABLE_VIOLATIONS = "violations"
DEFAULT_VIOLATION_LIMIT = 50         # Số bản ghi lịch sử mặc định
