import subprocess
import json

def check_wifi_speed_v2():
    print("Đang kiểm tra tốc độ qua CLI... (Vui lòng đợi)")
    try:
        # Chạy lệnh speedtest-cli và lấy kết quả dạng JSON
        # --secure giúp tránh lỗi kết nối HTTP
        result = subprocess.run(['speedtest-cli', '--json', '--secure'], 
                               capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            download = data['download'] / 10**6
            upload = data['upload'] / 10**6
            ping = data['ping']
            server = data['server']['sponsor']
            
            print("\n--- KẾT QUẢ ---")
            print(f"Server: {server}")
            print(f"Download: {download:.2f} Mbps")
            print(f"Upload: {upload:.2f} Mbps")
            print(f"Ping: {ping:.2f} ms")
        else:
            print("Lỗi: Không thể kết nối tới server Speedtest.")
            print(result.stderr)
            
    except FileNotFoundError:
        print("Lỗi: Bạn chưa cài đặt speedtest-cli. Hãy chạy: pip install speedtest-cli")
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    check_wifi_speed_v2()