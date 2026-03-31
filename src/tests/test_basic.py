import unittest
import os
import sys
import os

# Thêm đường dẫn src vào system path để import được module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DBManager
from core.ai_engine import AIEngine

class TestSentinelWarden(unittest.TestCase):
    def setUp(self):
        # Sử dụng database tạm thời cho testing
        self.db_path = "test_sentinel.db"
        self.db = DBManager(self.db_path)
        self.ai = AIEngine(model_path="yolov8n.pt")

    def tearDown(self):
        # Dọn dẹp sau khi test xong
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_database_init(self):
        """Kiểm tra khởi tạo Database và bảng logs"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
        table_exists = cursor.fetchone()
        self.assertIsNotNone(table_exists, "Bảng 'logs' phải được tạo tự động.")
        conn.close()

    def test_ai_engine_load(self):
        """Kiểm tra AI Engine có tải được model không"""
        self.assertIsNotNone(self.ai.model, "Model YOLO phải được tải thành công.")

if __name__ == '__main__':
    unittest.main()
