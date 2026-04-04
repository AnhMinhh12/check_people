"""
events/dispatcher.py — Event Dispatcher (Pub/Sub Pattern)

Skeleton module — Sẵn sàng tích hợp khi cần giao tiếp
giữa các module mà không tạo coupling trực tiếp.

Ví dụ ứng dụng:
  - Khi AI phát hiện vi phạm → Phát event → Module Telegram nhận và gửi thông báo
  - Khi camera mất kết nối → Phát event → Dashboard cập nhật trạng thái
"""
import logging
from enum import Enum
from typing import Callable, Dict, List

logger = logging.getLogger("EventDispatcher")


class EventType(Enum):
    """Danh sách các loại sự kiện trong hệ thống"""
    VIOLATION_DETECTED = "violation_detected"       # Phát hiện vi phạm mới
    VIOLATION_ENDED = "violation_ended"              # Kết thúc vi phạm (người quay lại)
    CAMERA_CONNECTED = "camera_connected"            # Camera kết nối thành công
    CAMERA_DISCONNECTED = "camera_disconnected"      # Camera mất tín hiệu
    SYSTEM_STARTED = "system_started"                # Hệ thống khởi động xong
    SYSTEM_SHUTDOWN = "system_shutdown"               # Hệ thống đang tắt


class EventDispatcher:
    """
    Bộ phát/nhận sự kiện trung tâm.

    Sử dụng:
        dispatcher = EventDispatcher()
        dispatcher.on(EventType.VIOLATION_DETECTED, lambda data: print(data))
        dispatcher.emit(EventType.VIOLATION_DETECTED, {"camera_id": 1})
    """

    def __init__(self):
        self._listeners: Dict[EventType, List[Callable]] = {}

    def on(self, event_type: EventType, callback: Callable):
        """Đăng ký listener cho một loại sự kiện"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        logger.debug(f"Đã đăng ký listener cho sự kiện: {event_type.value}")

    def off(self, event_type: EventType, callback: Callable):
        """Hủy đăng ký listener"""
        if event_type in self._listeners:
            self._listeners[event_type] = [cb for cb in self._listeners[event_type] if cb != callback]

    def emit(self, event_type: EventType, data: dict = None):
        """Phát sự kiện đến tất cả listener đã đăng ký"""
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(data or {})
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý sự kiện {event_type.value}: {e}")

    def clear(self):
        """Xóa toàn bộ listener (dùng khi shutdown)"""
        self._listeners.clear()


# Singleton — sử dụng chung trong toàn hệ thống
event_dispatcher = EventDispatcher()
