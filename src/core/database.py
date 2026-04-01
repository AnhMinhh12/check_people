import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger("WardenApp.Database")

class DatabaseManager:
    def __init__(self, db_path="sentinel.db", violations_dir="violations"):
        self.db_path = db_path
        self.violations_dir = violations_dir
        os.makedirs(self.violations_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT,
                    duration REAL DEFAULT 5.0,
                    image TEXT
                )
            ''')
            conn.commit()

    def add_violation(self, reason, filename):
        """Lưu bản ghi vi phạm mới"""
        time_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO violations (time, duration, image) VALUES (?, ?, ?)",
                    (time_str, 5.0, filename)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Lỗi Database: {e}")
            return False

    def get_recent_violations(self, limit=50):
        """Lấy lịch sử hiển thị Dashboard"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, time, duration, image FROM violations ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
            return [{"id": r[0], "time": r[1], "duration": r[2], "image": r[3]} for r in rows]
        except Exception as e:
            logger.error(f"Lỗi lấy lịch sử: {e}")
            return []
