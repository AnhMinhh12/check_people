"""
events/ — Quản lý phát/nhận sự kiện (Pub/Sub pattern, Event emitter)

Module này cung cấp cơ chế decoupled cho việc phát và lắng nghe sự kiện
trong hệ thống, giúp các module giao tiếp mà không phụ thuộc trực tiếp.

Ví dụ sử dụng:
    from events.dispatcher import event_dispatcher, EventType

    # Đăng ký listener
    event_dispatcher.on(EventType.VIOLATION_DETECTED, my_handler)

    # Phát sự kiện
    event_dispatcher.emit(EventType.VIOLATION_DETECTED, {"camera_id": 1, "duration": 10.5})
"""
