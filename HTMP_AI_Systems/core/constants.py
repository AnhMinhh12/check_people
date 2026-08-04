"""
core/constants.py — Hằng số hệ thống (không thay đổi theo môi trường)
"""

# Thông tin ứng dụng
APP_NAME = "Sentinel Warden AI"
APP_VERSION = "5.5"
APP_EDITION = "Enterprise"

# Trạng thái giám sát (Đồng bộ toàn dự án)
STATUS_WAITING = "ĐANG CHỜ"
STATUS_SAFE = "AN TOÀN"
STATUS_LEFT = "RỜI VỊ TRÍ"
STATUS_VIOLATION = "VI PHẠM"
STATUS_OFFLINE = "MẤT TÍN HIỆU"

# AI Engine defaults
DEFAULT_PERSISTENCE_FRAMES = 5      # Số frame giữ vết khi mất dấu người (chống nháy)
DEFAULT_ROI_WEB_SIZE = (640, 360)    # Kích thước chuẩn ROI trên Web
DEFAULT_NMS_IOU_THRESHOLD = 0.5      # Ngưỡng IoU cho chống đếm trùng
DEFAULT_STATUS_BUFFER_SEC = 1.0      # Bộ đệm xác nhận (giây) khi người QUAY LẠI (Chống nhiễu AI)

# Dashboard
DASHBOARD_JPEG_QUALITY = 75          # Chất lượng JPEG gửi lên Dashboard (Tăng từ 40 -> 75)
DASHBOARD_EMIT_HZ = 0.25            # Tần suất cập nhật Web (4 FPS)

# Live Grid Mode (Xem tất cả camera cùng lúc)
GRID_JPEG_QUALITY = 60               # Chất lượng JPEG cho grid (Tăng từ 30 -> 60)
GRID_FRAME_SIZE = (640, 360)         # Resolution cho grid (Tăng từ 320x180 -> 640x360)
GRID_EMIT_HZ = 0.05                  # Tần suất cập nhật (20 FPS)

# Database
DB_TABLE_CAMERAS = "cameras"
DB_TABLE_EVENTS = "events"
DEFAULT_HISTORY_LIMIT = 150           # Số bản ghi lịch sử mặc định
