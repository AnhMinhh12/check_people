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


    def sync_camera(self, name, url, group="Default"):
        """Đồng bộ camera từ config: Thêm mới nếu chưa có, cập nhật tên nếu URL đã có"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Kiểm tra xem URL đã tồn tại chưa
                cursor.execute("SELECT id, name FROM cameras WHERE url = ?", (url,))
                existing = cursor.fetchone()
                
                if existing:
                    cam_id, old_name = existing
                    if old_name != name:
                        cursor.execute("UPDATE cameras SET name = ?, group_name = ? WHERE id = ?", (name, group, cam_id))
                        logger.info(f"Đã cập nhật tên Camera ID {cam_id}: {old_name} -> {name}")
                else:
                    cursor.execute(
                        "INSERT INTO cameras (name, url, group_name) VALUES (?, ?, ?)",
                        (name, url, group)
                    )
                    logger.info(f"Đã thêm camera mới từ cấu hình: {name} ({url})")
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Lỗi đồng bộ camera: {e}")
            return False

    def delete_orphaned_cameras(self, active_urls):
        """Xóa vĩnh viễn các camera và dữ liệu liên quan nếu URL không nằm trong danh sách cấu hình"""
        if not active_urls:
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. Tìm các camera ID cần xóa
                placeholders = ",".join(["?"] * len(active_urls))
                cursor.execute(f"SELECT id FROM cameras WHERE url NOT IN ({placeholders})", active_urls)
                orphaned_ids = [row[0] for row in cursor.fetchall()]
                
                if orphaned_ids:
                    id_placeholders = ",".join(["?"] * len(orphaned_ids))
                    # 2. Xóa violations liên quan
                    cursor.execute(f"DELETE FROM violations WHERE camera_id IN ({id_placeholders})", orphaned_ids)
                    # 3. Xóa chính camera đó
                    cursor.execute(f"DELETE FROM cameras WHERE id IN ({id_placeholders})", orphaned_ids)
                    
                    conn.commit()
                    logger.info(f"Đã dọn dẹp {len(orphaned_ids)} camera cũ không còn trong cấu hình.")
                return True
        except Exception as e:
            logger.error(f"Lỗi khi dọn dẹp camera: {e}")
            return False

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
        """Lấy lịch sử hiển thị Dashboard (Có JOIN lấy tên Camera)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = """
                    SELECT v.id, v.time, v.duration, v.image, v.camera_id, c.name
                    FROM violations v
                    LEFT JOIN cameras c ON v.camera_id = c.id
                """
                if camera_id:
                    cursor.execute(query + " WHERE v.camera_id = ? ORDER BY v.id DESC LIMIT ?", (camera_id, limit))
                else:
                    cursor.execute(query + " ORDER BY v.id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
            return [{"id": r[0], "time": r[1], "duration": r[2], "image": r[3], "camera_id": r[4], "camera_name": r[5]} for r in rows]
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
