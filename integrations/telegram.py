"""
integrations/telegram.py — Tích hợp thông báo Telegram (Skeleton)

Skeleton module — Sẵn sàng tích hợp khi cần gửi cảnh báo vi phạm
qua Telegram Bot API.

Yêu cầu cấu hình trong .env:
    TELEGRAM_BOT_TOKEN=your_bot_token_here
    TELEGRAM_CHAT_ID=your_chat_id_here
"""
import os
import logging
import requests
from core.config import settings

logger = logging.getLogger("Telegram")


class TelegramNotifier:
    """
    Gửi thông báo cảnh báo qua Telegram Bot API.

    Sử dụng:
        notifier = TelegramNotifier()
        notifier.send_alert("Vi phạm tại Máy Hàn 01", image_path="violations/img.jpg")
    """

    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    @property
    def is_configured(self) -> bool:
        """Kiểm tra xem Telegram đã được cấu hình chưa"""
        return bool(self.bot_token and self.chat_id)

    def send_alert(self, message: str, image_path: str = None) -> bool:
        """
        Gửi cảnh báo text (và ảnh nếu có) qua Telegram

        Args:
            message: Nội dung cảnh báo
            image_path: Đường dẫn ảnh vi phạm (tùy chọn)

        Returns:
            True nếu gửi thành công, False nếu lỗi
        """
        if not self.is_configured:
            logger.warning("Telegram chưa được cấu hình (thiếu BOT_TOKEN hoặc CHAT_ID)")
            return False

        try:
            if image_path and os.path.exists(image_path):
                # Gửi ảnh kèm caption
                url = f"{self.base_url}/sendPhoto"
                with open(image_path, 'rb') as photo:
                    response = requests.post(url, data={
                        "chat_id": self.chat_id,
                        "caption": message
                    }, files={"photo": photo}, timeout=10)
            else:
                # Gửi text thuần
                url = f"{self.base_url}/sendMessage"
                response = requests.post(url, data={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }, timeout=10)

            if response.status_code == 200:
                logger.info(f"Đã gửi cảnh báo Telegram: {message[:50]}...")
                return True
            else:
                logger.error(f"Telegram API lỗi {response.status_code}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Lỗi gửi Telegram: {e}")
            return False
