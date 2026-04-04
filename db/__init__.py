# db/ — Tương tác với cơ sở dữ liệu (ORM, connection, repository)
#
# Cấu trúc:
#   connection.py  — Engine, Session, pooling (SQLAlchemy)
#   models.py      — ORM models (Camera, Violation)
#   repository.py  — Repository Pattern (CameraRepository, ViolationRepository)
from db.connection import get_session, init_db
from db.repository import CameraRepository, ViolationRepository
