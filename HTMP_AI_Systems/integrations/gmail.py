"""
integrations/gmail.py — Module gửi thông báo qua Gmail SMTP
"""
import smtplib
import threading
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from core.config import settings

logger = logging.getLogger("GmailNotifier")

class GmailNotifier:
    """
    Hỗ trợ gửi thông báo vi phạm qua Gmail SMTP.
    Sử dụng Threading để không làm gián đoạn luồng xử lý AI.
    """

    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.recipients = settings.recipient_list

    @property
    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_password and self.recipients)

    def send_violation_alert(self, camera_name: str, zone_name: str, duration: float, timestamp: str = None, snapshot_path: str = None):
        """
        Gửi cảnh báo vi phạm (Chạy trong thread riêng)
        """
        if not self.is_configured:
            logger.warning("Gmail SMTP chưa được cấu hình đầy đủ trong .env")
            return

        thread = threading.Thread(
            target=self._send_email_sync,
            args=(camera_name, zone_name, duration, timestamp, snapshot_path),
            daemon=True
        )
        thread.start()

    def _send_email_sync(self, camera_name: str, zone_name: str, duration: float, timestamp: str, snapshot_path: str):
        """Hàm thực thi gửi email đồng bộ (được gọi từ thread)"""
        try:
            msg = MIMEMultipart()
            msg['From'] = f"Sentinel AI Warden <{self.smtp_user}>"
            msg['To'] = ", ".join(self.recipients)
            msg['Subject'] = f"🚨 CẢNH BÁO VI PHẠM: {camera_name.upper()} - {zone_name.upper()}"

            # Nội dung HTML
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                        <h2 style="color: #d9534f; border-bottom: 2px solid #d9534f; padding-bottom: 10px;">
                            Phát hiện vi phạm vắng mặt!
                        </h2>
                        <p>Hệ thống Sentinel Warden AI đã ghi nhận một trường hợp vi phạm tại:</p>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px; font-weight: bold; width: 120px;">Thời gian:</td>
                                <td style="padding: 8px;">{timestamp or "Không xác định"}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Camera:</td>
                                <td style="padding: 8px;">{camera_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Vị trí (Zone):</td>
                                <td style="padding: 8px;">{zone_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; font-weight: bold;">Thời gian vắng:</td>
                                <td style="padding: 8px; color: #d9534f;">{duration} giây</td>
                            </tr>
                        </table>
                        <p style="margin-top: 20px;">Vui lòng kiểm tra tình hình thực tế.</p>
                        <hr style="border: 0; border-top: 1px solid #eee;">
                        <p style="font-size: 12px; color: #777;">Thông báo tự động từ hệ thống giám sát Sentinel AI Warden.</p>
                    </div>
                </body>
            </html>
            """
            msg.attach(MIMEText(html, 'html'))

            # Đính kèm ảnh nếu có
            if snapshot_path and os.path.exists(snapshot_path):
                with open(snapshot_path, 'rb') as f:
                    img_data = f.read()
                    image = MIMEImage(img_data, name=os.path.basename(snapshot_path))
                    msg.attach(image)

            # Kết nối và gửi
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Bảo mật TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Đã gửi email cảnh báo vi phạm tại {camera_name} -> {zone_name}")

        except Exception as e:
            logger.error(f"❌ Lỗi gửi email Gmail: {e}")

# Singleton instance
gmail_notifier = GmailNotifier()
