import speedtest

def check_wifi_speed():
    print("Đang khởi tạo bài kiểm tra... Vui lòng đợi (có thể mất 30s)")
    
    # Khởi tạo đối tượng Speedtest
    st = speedtest.Speedtest()
    
    # Tìm server tốt nhất dựa trên ping
    st.get_best_server()
    
    print("Đang đo tốc độ Download...")
    download_speed = st.download()
    
    print("Đang đo tốc độ Upload...")
    upload_speed = st.upload()
    
    ping = st.results.ping

    # Chuyển đổi từ bits/s sang Mbps (1 Mbps = 10^6 bits)
    print("\n--- KẾT QUẢ ---")
    print(f"Server: {st.results.server['sponsor']} ({st.results.server['name']})")
    print(f"Tốc độ Download: {download_speed / 10**6:.2f} Mbps")
    print(f"Tốc độ Upload: {upload_speed / 10**6:.2f} Mbps")
    print(f"Độ trễ (Ping): {ping:.2f} ms")

if __name__ == "__main__":
    check_wifi_speed()