"""
db/models.py — Định nghĩa cấu trúc các bảng chuyên nghiệp (PostgreSQL)

Bảng:
  - cameras:       Danh sách camera (Thêm location, resolution, metadata)
  - zones:         Vùng nhận diện ROI (Đa giác, loại vi phạm, ngưỡng thời gian)
  - events:         Nhật ký vi phạm (Liên kết camera + zone, start/end time)
  - system_health: Giám sát tài nguyên máy chủ (GPU, FPS, Heartbeat)
"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Index, BigInteger, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base


class Camera(Base):
    """Bảng quản lý danh sách Camera giám sát"""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="Tên camera hiển thị")
    url = Column(Text, nullable=False, comment="RTSP URL")
    location = Column(String(255), nullable=True, comment="Vị trí vật lý")
    resolution = Column(String(50), nullable=True)
    fps = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True, comment="Cấu hình mở rộng")
    created_at = Column(DateTime, server_default=func.now())

    # Quan hệ
    zones = relationship("Zone", back_populates="camera", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="camera")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "location": self.location,
            "active": self.is_active,
            "metadata": self.metadata_json,
        }


class Zone(Base):
    """Bảng định nghĩa vùng nhận diện (ROI)"""
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    zone_name = Column(String(255), nullable=False)
    type = Column(String(50), comment="Loại nhận diện: absence, restricted...")
    roi_polygon = Column(JSON, comment="Mảng tọa độ [[x,y],...]")
    threshold_seconds = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Quan hệ
    camera = relationship("Camera", back_populates="zones")
    events = relationship("Event", back_populates="zone")

    def to_dict(self):
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "name": self.zone_name,
            "type": self.type,
            "roi": self.roi_polygon,
            "active": self.is_active
        }


class Event(Base):
    """Bảng nhật ký sự kiện/vi phạm — đổi tên từ Violation sang Event"""
    __tablename__ = "events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(100), comment="Dòng sự kiện")
    start_time = Column(DateTime, server_default=func.now())
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, default=0.0)
    snapshot_path = Column(Text, comment="Đường dẫn ảnh chứng cứ")
    status = Column(String(50), default="unreviewed")
    machines_involved = Column(Text, nullable=True, comment="Danh sách các máy vi phạm cùng lúc")

    # Quan hệ
    camera = relationship("Camera", back_populates="events")
    zone = relationship("Zone", back_populates="events")

    __table_args__ = (
        Index("idx_events_camera", "camera_id"),
        Index("idx_events_zone", "zone_id"),
        Index("idx_events_time", "start_time"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "camera_name": self.camera.name if self.camera else f"CAM-{self.camera_id}",
            "zone_id": self.zone_id,
            "zone_name": self.zone.zone_name if self.zone else "Global",
            "machine_name": self.machines_involved if self.machines_involved else (self.zone.zone_name if self.zone else "Toàn cảnh"),
            "type": self.event_type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "time": self.start_time.strftime("%H:%M:%S %d/%m/%Y") if self.start_time else "N/A",
            "duration": self.duration,
            "image": self.snapshot_path,
            "status": self.status
        }


class SystemHealth(Base):
    """Bảng giám sát sức khỏe máy chủ AI"""
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_name = Column(String(100), nullable=False)
    gpu_load = Column(Integer)
    memory_usage = Column(Integer)
    fps_current = Column(Float)
    last_heartbeat = Column(DateTime, server_default=func.now(), onupdate=func.now())
