import sqlite3
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("WardenApp.Database")

class DBManager:
    def __init__(self, db_path, violations_dir, old_json_path=None):
        self.db_path = db_path
        self.violations_dir = violations_dir
        self.old_json_path = old_json_path
        os.makedirs(self.violations_dir, exist_ok=True)
        self.init_db()

    def init_db(self):
        """Khởi tạo SQLite và chuyển đổi dữ liệu từ JSON nếu có"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT,
                duration REAL,
                image TEXT
            )
        ''')
        conn.commit()

        # Kiểm tra migration từ JSON cũ
        if self.old_json_path and os.path.exists(self.old_json_path):
            logger.info("Phát hiện file dữ liệu cũ (JSON). Đang tiến hành chuyển đổi sang Database...")
            try:
                with open(self.old_json_path, "r") as f:
                    history = json.load(f)
                
                for entry in reversed(history):
                    cursor.execute(
                        "INSERT INTO violations (time, duration, image) VALUES (?, ?, ?)",
                        (entry.get("time"), entry.get("duration"), entry.get("image"))
                    )
                conn.commit()
                
                # Đổi tên file cũ để tránh migrate lại lần sau
                os.rename(self.old_json_path, self.old_json_path + ".bak")
                logger.info(f"Đã chuyển đổi thành công {len(history)} bản ghi. File cũ đã được lưu thành .bak")
            except Exception as e:
                logger.error(f"Lỗi khi chuyển đổi dữ liệu: {e}")
        
        conn.close()

    def get_history(self, limit=100):
        """Lấy lịch sử vi phạm"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, time, duration, image FROM violations ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "id": r[0],
                    "time": r[1],
                    "duration": r[2],
                    "image": r[3]
                } for r in rows
            ]
        except Exception as e:
            logger.error(f"Lỗi lấy lịch sử: {e}")
            return []

    def save_violation(self, frame_bytes, duration):
        """Lưu ảnh và log vi phạm vào database"""
        import cv2
        import numpy as np
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"violation_{timestamp}.jpg"
        filepath = os.path.join(self.violations_dir, filename)
        
        # Lưu ảnh từ bytes (hoặc frame nếu truyền vào)
        # Ở đây ta giả định nhận vào frame numpy từ AIWorker
        cv2.imwrite(filepath, frame_bytes)
        
        time_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO violations (time, duration, image) VALUES (?, ?, ?)",
                (time_str, round(duration, 1), filename)
            )
            conn.commit()
            violation_id = cursor.lastrowid
            conn.close()
            
            return {
                "id": violation_id,
                "time": time_str,
                "duration": round(duration, 1),
                "image": filename
            }
        except Exception as e:
            logger.error(f"Lỗi lưu Database: {e}")
            return None

    def update_duration(self, violation_id, duration):
        """Cập nhật thời lượng cho bản ghi vi phạm"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE violations SET duration = ? WHERE id = ?",
                (round(duration, 1), violation_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Lỗi update Database: {e}")
            return False
