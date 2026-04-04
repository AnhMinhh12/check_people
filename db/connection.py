"""
db/connection.py — Quản lý kết nối cơ sở dữ liệu, pooling và phiên làm việc (session)

Hỗ trợ:
  - SQLite (Dev/Local):  sqlite:///data/sentinel.db
  - MySQL  (Production): mysql+pymysql://user:pass@host:3306/dbname

Sử dụng:
    from db.connection import get_session, init_db

    # Khởi tạo tables (gọi 1 lần khi khởi động)
    init_db()

    # Sử dụng session trong nghiệp vụ
    with get_session() as session:
        cameras = session.query(Camera).all()
"""
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

logger = logging.getLogger("Database.Connection")

# Base class cho tất cả ORM models
Base = declarative_base()

# Tạo Engine theo DATABASE_URL từ cấu hình
# SQLite: không cần pool, dùng check_same_thread=False cho multi-thread
# MySQL:  pool_size + pool_recycle để tái sử dụng kết nối hiệu quả
_engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "echo": False,
    }
else:
    _engine_kwargs = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,   # Tái tạo kết nối sau 1 giờ (tránh MySQL timeout)
        "pool_pre_ping": True,  # Kiểm tra kết nối trước khi dùng
        "echo": False,
    }

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

# Session factory — mỗi lần gọi tạo 1 session mới
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_session():
    """
    Context manager cung cấp phiên làm việc (session) an toàn.
    Tự động commit nếu thành công, rollback nếu lỗi, và đóng session.

    Sử dụng:
        with get_session() as session:
            session.add(obj)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Tạo tất cả bảng trong database (nếu chưa tồn tại)"""
    # Import models để Base biết về các bảng
    import db.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database đã khởi tạo thành công: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
