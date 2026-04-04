"""
db/models.py — Định nghĩa cấu trúc các bảng trong cơ sở dữ liệu (ORM)

Bảng:
  - cameras:    Danh sách camera giám sát
  - violations: Nhật ký vi phạm (liên kết với camera qua ForeignKey)
"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.connection import Base


class Camera(Base):
    """Bảng quản lý danh sách Camera giám sát"""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="Tên camera hiển thị")
    url = Column(Text, nullable=False, comment="RTSP URL")
    group_name = Column(String(255), default="Default", comment="Nhóm/Khu vực")
    is_active = Column(Integer, default=1, comment="1=Hoạt động, 0=Tạm dừng")

    # Quan hệ 1-N: Một camera có nhiều vi phạm
    violations = relationship("Violation", back_populates="camera", cascade="all, delete-orphan")

    def to_dict(self):
        """Chuyển đổi sang dictionary cho JSON response"""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "group": self.group_name,
            "active": self.is_active,
        }

    def __repr__(self):
        return f"<Camera(id={self.id}, name='{self.name}')>"


class Violation(Base):
    """Bảng nhật ký vi phạm — ghi lại mỗi lần vắng mặt quá thời gian cho phép"""
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), comment="ID camera phát hiện")
    time = Column(String(50), comment="Thời điểm bắt đầu vi phạm")
    duration = Column(Float, default=5.0, comment="Thời lượng vắng mặt (giây)")
    image = Column(Text, comment="Tên file ảnh bằng chứng")

    # Quan hệ N-1: Nhiều vi phạm thuộc về một camera
    camera = relationship("Camera", back_populates="violations")

    # Chỉ mục để truy vấn nhanh
    __table_args__ = (
        Index("idx_violations_camera", "camera_id"),
        Index("idx_violations_time", "time"),
    )

    def to_dict(self):
        """Chuyển đổi sang dictionary cho JSON response"""
        return {
            "id": self.id,
            "time": self.time,
            "duration": self.duration,
            "image": self.image,
            "camera_id": self.camera_id,
            "camera_name": self.camera.name if self.camera else None,
        }

    def __repr__(self):
        return f"<Violation(id={self.id}, camera_id={self.camera_id}, time='{self.time}')>"
