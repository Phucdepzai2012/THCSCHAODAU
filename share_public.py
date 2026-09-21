# -*- coding: utf-8 -*-
"""
THCS NGO VAN SO - PUBLIC COMMUNITY LINK LAUNCHER
Tự động khởi chạy máy chủ Cổng thông tin và tạo đường Link Trực tuyến (Public Internet URL)
để gửi cho cộng đồng, phụ huynh, giáo viên và học sinh truy cập từ bất kỳ đâu.
"""

import os
import sys
import time
import socket
import subprocess
import threading
import re

PORT = 5000
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_URL_FILE = os.path.join(CURRENT_DIR, 'public_url.txt')

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def start_flask_app():
    """Khởi chạy máy chủ web Flask"""
    app_script = os.path.join(CURRENT_DIR, 'app.py')
    subprocess.Popen([sys.executable, app_script], cwd=CURRENT_DIR)

def start_pinggy_tunnel():
    """Khởi chạy SSH Pinggy Tunnel để nhận link HTTPS công khai"""
    print("\n[+] Đang tạo đường Link Online cho cộng đồng...")
    
    cmd = [
        "ssh", "-p", "443",
        "-R0:localhost:5000",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "a.pinggy.io"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        public_url = None
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            # Tìm link http/https trong output
            matches = re.findall(r'https?://[a-zA-Z0-9.-]+\.pinggy\.link', line)
            if not matches:
                matches = re.findall(r'https?://[^\s]+', line)
            
            for m in matches:
                if 'pinggy.link' in m:
                    public_url = m
                    break
            
            if public_url:
                with open(PUBLIC_URL_FILE, 'w', encoding='utf-8') as f:
                    f.write(public_url)
                
                local_ip = get_local_ip()
                print("\n" + "="*70)
                print(" 🎉  CỔNG THÔNG TIN ĐIỆN TỬ ĐÃ SẴN SÀNG CHO CỘNG ĐỒNG!")
                print("="*70)
                print(f" 🌐  LINK TRỰC TUYẾN TOÀN CẦU (Gửi cho cộng đồng, phụ huynh, học sinh):")
                print(f"     👉  {public_url}")
                print(f"\n 📶  LINK MẠNG NỘI BỘ (Dùng chung Wi-Fi):")
                print(f"     👉  http://{local_ip}:{PORT}")
                print(f"\n 🔐  TRANG ĐĂNG NHẬP QUẢN TRỊ (ADMIN):")
                print(f"     👉  {public_url}/admin/login")
                print("="*70)
                print("\n (*) Lưu ý: Hãy giữ cửa sổ này mở để mọi người luôn vào được website.")
                print("     Mọi bài viết, banner bạn đăng sẽ hiển thị tức thì trên link này!\n")
                break

        process.wait()
    except Exception as e:
        print(f"[-] Lỗi khi tạo tunnel: {e}")
        local_ip = get_local_ip()
        print(f"[!] Bạn vẫn có thể truy cập qua link nội bộ: http://{local_ip}:{PORT}")

if __name__ == '__main__':
    # 1. Khởi chạy Flask
    flask_thread = threading.Thread(target=start_flask_app, daemon=True)
    flask_thread.start()
    time.sleep(2)
    
    # 2. Tạo Public Tunnel
    start_pinggy_tunnel()
