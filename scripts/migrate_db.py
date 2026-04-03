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
        
        # 3. Đồng bộ camera từ .env
        camera_configs = []
        default_rtsp = os.getenv("RTSP_URL")
        if default_rtsp:
            camera_configs.append(("Camera Mặc Định", default_rtsp))
        for i in range(1, 101):
            url = os.getenv(f"RTSP_URL{i}")
            if url:
                name = os.getenv(f"CAMERA_NAME{i}", f"Camera {i}")
                camera_configs.append((name, url))

        for name, url in camera_configs:
            # Kiểm tra URL đã tồn tại chưa
            cursor.execute("SELECT id FROM cameras WHERE url = ?", (url,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO cameras (name, url, group_name) VALUES (?, ?, ?)",
                    (name, url, "Zone A")
                )
                print(f"Đã thêm camera mới: {name}")
            else:
                cursor.execute("UPDATE cameras SET name = ? WHERE url = ?", (name, url))
                print(f"Đã cập nhật tên cho camera: {name}")

        # 4. DỌN DẸP: Xóa camera không còn trong env
        active_urls = [cfg[1] for cfg in camera_configs]
        if active_urls:
            placeholders = ",".join(["?"] * len(active_urls))
            cursor.execute(f"DELETE FROM violations WHERE camera_id NOT IN (SELECT id FROM cameras WHERE url IN ({placeholders}))", active_urls)
            cursor.execute(f"DELETE FROM cameras WHERE url NOT IN ({placeholders})", active_urls)
            print("Đã dọn dẹp các camera cũ khỏi Database.")

        # 5. Tạo Index
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_time ON violations(time)')
        
        conn.commit()
    print("Migration hoàn tất.")

if __name__ == "__main__":
    migrate()
