"""
integrations/ — Tích hợp với hệ thống bên ngoài (ERP, WebSockets, Telegram, v.v.)

Module này chứa các adapter kết nối với dịch vụ bên thứ ba.
Mỗi integration nên là một file/class riêng biệt.

Ví dụ sử dụng:
    from integrations.telegram import TelegramNotifier
    notifier = TelegramNotifier(bot_token="...", chat_id="...")
    notifier.send_alert("Vi phạm tại Camera 1!")
"""
