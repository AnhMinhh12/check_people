import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger("WardenApp.Database")

class DatabaseManager:
    def __init__(self, db_path=None, violations_dir=None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", "data/sentinel.db")
        self.violations_dir = violations_dir or os.getenv("VIOLATIONS_DIR", "data/violations")
        os.makedirs(self.violations_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Bảng quản lý Danh sách Camera
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cameras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    group_name TEXT DEFAULT 'Default',
                    is_active INTEGER DEFAULT 1
                )
            ''')
            # Bảng Nhật ký Vi phạm (Có camera_id và Index để tối ưu 100+ cam)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id INTEGER,
                    time TEXT,
                    duration REAL DEFAULT 5.0,
                    image TEXT,
                    FOREIGN KEY (camera_id) REFERENCES cameras (id)
                )
            ''')
            # Tạo chỉ mục để truy vấn báo cáo theo camera cực nhanh
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_camera ON violations(camera_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_time ON violations(time)')
            conn.commit()

    def add_violation(self, camera_id, filename, duration=5.0):
        """Lưu bản ghi vi phạm mới kèm theo thời lượng và ID camera"""
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO violations (camera_id, time, duration, image) VALUES (?, ?, ?, ?)",
                    (camera_id, time_str, duration, filename)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Lỗi Database (add_violation): {e}")
            return False

    def add_camera(self, name, url, group="Default"):
        """Thêm camera mới vào hệ thống"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO cameras (name, url, group_name) VALUES (?, ?, ?)",
                    (name, url, group)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Lỗi thêm camera: {e}")
            return None

    def get_cameras(self, active_only=True):
        """Lấy danh sách camera"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = "SELECT id, name, url, group_name, is_active FROM cameras"
                if active_only: query += " WHERE is_active = 1"
                cursor.execute(query)
                rows = cursor.fetchall()
            return [{"id": r[0], "name": r[1], "url": r[2], "group": r[3], "active": r[4]} for r in rows]
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách camera: {e}")
            return []

    def get_recent_violations(self, camera_id=None, limit=50):
        """Lấy lịch sử hiển thị Dashboard (Có lọc theo camera)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if camera_id:
                    cursor.execute("SELECT id, time, duration, image, camera_id FROM violations WHERE camera_id = ? ORDER BY id DESC LIMIT ?", (camera_id, limit))
                else:
                    cursor.execute("SELECT id, time, duration, image, camera_id FROM violations ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
            return [{"id": r[0], "time": r[1], "duration": r[2], "image": r[3], "camera_id": r[4]} for r in rows]
        except Exception as e:
            logger.error(f"Lỗi lấy lịch sử: {e}")
            return []

    def get_analytics(self, camera_id=None):
        """Thống kê chi tiết từng camera phục vụ trang Phân Tích"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Đếm số lần vi phạm
                q = "SELECT COUNT(*) FROM violations"
                if camera_id: cursor.execute(q + " WHERE camera_id = ?", (camera_id,))
                else: cursor.execute(q)
                count = cursor.fetchone()[0]
                
                # Tính tổng thời gian rời máy
                q = "SELECT SUM(duration) FROM violations"
                if camera_id: cursor.execute(q + " WHERE camera_id = ?", (camera_id,))
                else: cursor.execute(q)
                total_duration = cursor.fetchone()[0] or 0
                
            return {"total_violations": count, "total_duration_minutes": round(total_duration / 60, 1)}
        except Exception as e:
            logger.error(f"Lỗi Analytics: {e}")
            return {"total_violations": 0, "total_duration_minutes": 0}
