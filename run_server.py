import os
from waitress import serve
from app import app, FLASK_PORT
from dotenv import load_dotenv
import logging

# Tải cấu hình
load_dotenv()

# Cấu hình logging cho production
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WaitressServer")

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    logger.info(f"Đang khởi chạy Production Server (Waitress) trên cổng {port}...")
    logger.info("Lưu ý: Waitress sẽ sử dụng cơ chế Long Polling cho Socket.IO trên Windows.")
    
    # Chạy server
    # threads=6 giúp xử lý nhiều yêu cầu cùng lúc (tốt cho webcam stream)
    serve(app, host='0.0.0.0', port=port, threads=6)
