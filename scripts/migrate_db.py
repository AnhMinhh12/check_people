from dotenv import load_dotenv
load_dotenv()

db_path = os.getenv("DATABASE_PATH", "data/sentinel.db")

def migrate():
    if not os.path.exists(db_path):
        print("Database not found, nothing to migrate.")
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Thêm cột camera_id vào bảng violations nếu chưa có
        try:
            cursor.execute("ALTER TABLE violations ADD COLUMN camera_id INTEGER DEFAULT 1")
            print("Đã thêm cột camera_id vào violations.")
        except sqlite3.OperationalError:
            print("Cột camera_id đã tồn tại.")

        # 2. Tạo bảng cameras nếu chưa có
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                group_name TEXT DEFAULT 'Default',
                is_active INTEGER DEFAULT 1
            )
        ''')
        print("Đã xác nhận bảng cameras tồn tại.")
        
        # 3. Thêm camera mặc định nếu bảng trốn
        cursor.execute("SELECT COUNT(*) FROM cameras")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO cameras (name, url, group_name) VALUES (?, ?, ?)",
                ("Camera Mặc Định", os.getenv("RTSP_URL", "rtsp://admin:pass@192.168.1.10:554/stream"), "Zone A")
            )
            print("Đã thêm camera mặc định.")

        # 4. Tạo Index
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_camera ON violations(camera_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_time ON violations(time)')
        
        conn.commit()
    print("Migration hoàn tất.")

if __name__ == "__main__":
    migrate()
