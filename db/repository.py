"""
db/repository.py — Repository Pattern: tách biệt logic SQL khỏi logic nghiệp vụ

Các class:
  - CameraRepository:    CRUD + đồng bộ camera từ .env
  - ViolationRepository: Ghi vi phạm, truy vấn lịch sử, thống kê

Sử dụng:
    from db.repository import CameraRepository, ViolationRepository

    cam_repo = CameraRepository()
    cameras = cam_repo.get_all()
    cam_repo.sync("Máy Hàn 01", "rtsp://...", "Zone A")

    vio_repo = ViolationRepository()
    vio_repo.add(camera_id=1, filename="violation_001.jpg", duration=10.5)
"""
import logging
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from db.connection import get_session
from db.models import Camera, Violation

logger = logging.getLogger("Database.Repository")


class CameraRepository:
    """Repository quản lý bảng cameras — tách biệt truy vấn khỏi nghiệp vụ"""

    def get_all(self, active_only=True) -> list:
        """Lấy danh sách camera"""
        try:
            with get_session() as session:
                query = session.query(Camera)
                if active_only:
                    query = query.filter(Camera.is_active == 1)
                cameras = query.all()
                return [cam.to_dict() for cam in cameras]
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách camera: {e}")
            return []

    def get_by_id(self, camera_id: int):
        """Lấy thông tin 1 camera theo ID"""
        try:
            with get_session() as session:
                camera = session.query(Camera).filter(Camera.id == camera_id).first()
                return camera.to_dict() if camera else None
        except Exception as e:
            logger.error(f"Lỗi lấy camera ID {camera_id}: {e}")
            return None

    def sync(self, name: str, url: str, group: str = "Default") -> bool:
        """
        Đồng bộ camera từ config:
          - Thêm mới nếu URL chưa có
          - Cập nhật tên nếu URL đã tồn tại
        """
        try:
            with get_session() as session:
                existing = session.query(Camera).filter(Camera.url == url).first()

                if existing:
                    if existing.name != name:
                        old_name = existing.name
                        existing.name = name
                        existing.group_name = group
                        logger.info(f"Đã cập nhật tên Camera ID {existing.id}: {old_name} -> {name}")
                else:
                    new_camera = Camera(name=name, url=url, group_name=group)
                    session.add(new_camera)
                    logger.info(f"Đã thêm camera mới từ cấu hình: {name} ({url})")

                return True
        except Exception as e:
            logger.error(f"Lỗi đồng bộ camera: {e}")
            return False

    def delete_orphaned(self, active_urls: list) -> bool:
        """Xóa vĩnh viễn các camera không còn trong danh sách cấu hình .env"""
        if not active_urls:
            return False
        try:
            with get_session() as session:
                orphaned = session.query(Camera).filter(Camera.url.notin_(active_urls)).all()

                if orphaned:
                    count = len(orphaned)
                    for cam in orphaned:
                        session.delete(cam)  # cascade xóa violations liên quan
                    logger.info(f"Đã dọn dẹp {count} camera cũ không còn trong cấu hình.")

                return True
        except Exception as e:
            logger.error(f"Lỗi khi dọn dẹp camera: {e}")
            return False


class ViolationRepository:
    """Repository quản lý bảng violations — ghi nhận và truy vấn vi phạm"""

    def add(self, camera_id: int, filename: str, duration: float = 5.0) -> bool:
        """Lưu bản ghi vi phạm mới kèm thời lượng và ID camera"""
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with get_session() as session:
                violation = Violation(
                    camera_id=camera_id,
                    time=time_str,
                    duration=duration,
                    image=filename,
                )
                session.add(violation)
            return True
        except Exception as e:
            logger.error(f"Lỗi Database (add_violation): {e}")
            return False

    def get_recent(self, camera_id: int = None, limit: int = 50) -> list:
        """Lấy lịch sử vi phạm gần nhất (có JOIN lấy tên Camera)"""
        try:
            with get_session() as session:
                query = session.query(Violation).options(
                    joinedload(Violation.camera)
                )
                if camera_id:
                    query = query.filter(Violation.camera_id == camera_id)

                violations = query.order_by(Violation.id.desc()).limit(limit).all()
                return [v.to_dict() for v in violations]
        except Exception as e:
            logger.error(f"Lỗi lấy lịch sử: {e}")
            return []

    def get_analytics(self, camera_id: int = None) -> dict:
        """Thống kê chi tiết vi phạm (tổng số lần, tổng thời gian rời máy)"""
        try:
            with get_session() as session:
                query = session.query(
                    func.count(Violation.id).label("total"),
                    func.coalesce(func.sum(Violation.duration), 0).label("total_duration"),
                )
                if camera_id:
                    query = query.filter(Violation.camera_id == camera_id)

                result = query.one()
                return {
                    "total_violations": result.total,
                    "total_duration_minutes": round(result.total_duration / 60, 1),
                }
        except Exception as e:
            logger.error(f"Lỗi Analytics: {e}")
            return {"total_violations": 0, "total_duration_minutes": 0}
