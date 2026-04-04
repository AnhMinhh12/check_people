"""
integrations/erp.py — Tích hợp hệ thống ERP (Skeleton)

Skeleton module — Sẵn sàng tích hợp khi cần đồng bộ dữ liệu vi phạm
với hệ thống quản lý sản xuất (ERP/MES).

Yêu cầu cấu hình trong .env:
    ERP_API_URL=https://erp.company.com/api
    ERP_API_KEY=your_api_key_here
"""
import os
import logging
import requests

logger = logging.getLogger("ERP")


class ERPConnector:
    """
    Đồng bộ dữ liệu vi phạm với hệ thống ERP/MES.

    Sử dụng:
        connector = ERPConnector()
        connector.sync_violation(camera_id=1, duration=15.0, timestamp="2026-04-04 10:30:00")
    """

    def __init__(self, api_url=None, api_key=None):
        self.api_url = api_url or os.getenv("ERP_API_URL")
        self.api_key = api_key or os.getenv("ERP_API_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_key)

    def sync_violation(self, camera_id: int, duration: float, timestamp: str) -> bool:
        """
        Gửi bản ghi vi phạm lên ERP

        Args:
            camera_id: ID camera phát hiện vi phạm
            duration: Thời lượng vắng mặt (giây)
            timestamp: Thời điểm vi phạm

        Returns:
            True nếu đồng bộ thành công
        """
        if not self.is_configured:
            logger.warning("ERP chưa được cấu hình")
            return False

        try:
            response = requests.post(
                f"{self.api_url}/violations",
                json={
                    "camera_id": camera_id,
                    "duration_seconds": duration,
                    "timestamp": timestamp,
                    "source": "sentinel_warden_ai"
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            return response.status_code in (200, 201)

        except Exception as e:
            logger.error(f"Lỗi đồng bộ ERP: {e}")
            return False
