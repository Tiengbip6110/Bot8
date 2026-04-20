import os
import requests
import threading
import time
from colorama import Fore, init
import certifi

# Khởi tạo colorama để hỗ trợ màu sắc trên Windows
init()

# Constants
N_THREADS = 50  # Số luồng tối đa, giảm để tránh quá tải
threads = []
stop_event = threading.Event()  # Để dừng các luồng một cách an toàn

# Nhập link bài viết
print('[==================[TOOL BY @sfvbnr]==================]')
import sys
link1 = sys.argv[1] if len(sys.argv) > 1 else ''
print('-------------------- Tool Started --------------------')

# Kiểm tra định dạng link
if not link1.startswith('https://t.me/'):
    print(Fore.RED + "Lỗi: Link bài viết không đúng định dạng! Vui lòng nhập link dạng https://t.me/channel_name/message_id")
    exit()

def validate_proxy(proxy):
    """Kiểm tra xem proxy có hoạt động và hỗ trợ HTTPS không"""
    try:
        proxies = {'http': f'http://{proxy}', 'https': f'https://{proxy}'}
        response = requests.get('https://api.ipify.org', proxies=proxies, timeout=5, verify=certifi.where())
        if response.status_code == 200:
            print(Fore.GREEN + f"Proxy {proxy} hoạt động và hỗ trợ HTTPS!")
            return True
        return False
    except Exception as e:
        print(Fore.YELLOW + f"Proxy {proxy} không hoạt động hoặc không hỗ trợ HTTPS: {e}")
        return False

def view2(proxy):
    """Gửi view bằng proxy"""
    try:
        channel = link1.split('/')[3]
        msgid = link1.split('/')[4]
        send_seen(channel, msgid, proxy)
    except IndexError:
        print(Fore.RED + "Lỗi: Link bài viết không đúng định dạng!")
    except Exception as e:
        print(Fore.RED + f"Lỗi gửi view: {e}")

def send_seen(channel, msgid, proxy):
    """Gửi view đến bài viết trên Telegram"""
    s = requests.Session()
    proxies = {'http': f'http://{proxy}', 'https': f'https://{proxy}'}

    try:
        response = s.get(f"https://t.me/{channel}/{msgid}", timeout=10, proxies=proxies, verify=certifi.where())
        cookie = response.headers.get('set-cookie', '').split(';')[0]
        if not cookie:
            print(Fore.YELLOW + f"Proxy {proxy}: Không nhận được cookie!")
            return
    except requests.RequestException as e:
        print(Fore.YELLOW + f"Proxy {proxy}: Lỗi kết nối - {e}")
        return

    headers = {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": cookie,
        "Referer": f"https://t.me/{channel}/{msgid}?embed=1"
    }
    data = {"_rl": "1"}

    try:
        response = s.post(f'https://t.me/{channel}/{msgid}?embed=1', json=data, headers=headers, proxies=proxies, verify=certifi.where())
        key = response.text.split('data-view="')[1].split('"')[0]
    except (requests.RequestException, IndexError) as e:
        print(Fore.YELLOW + f"Proxy {proxy}: Lỗi gửi POST - {e}")
        return

    try:
        response = s.get(f'https://t.me/v/?views={key}', timeout=10, headers=headers, proxies=proxies, verify=certifi.where())
        if response.text == "true":
            print(Fore.LIGHTGREEN_EX + f'View sent [✅] - Proxy: {proxy}')
        else:
            print(Fore.YELLOW + f"Proxy {proxy}: View không thành công!")
    except requests.RequestException as e:
        print(Fore.YELLOW + f"Proxy {proxy}: Lỗi xác nhận view - {e}")

def checker(proxy):
    """Luồng chạy gửi view"""
    while not stop_event.is_set():
        try:
            view2(proxy)
        except Exception as e:
            print(Fore.RED + f"Lỗi trong checker (Proxy {proxy}): {e}")
        time.sleep(1)  # Nghỉ để tránh quá tải

def start():
    """Bắt đầu tool và chạy liên tục"""
    if not os.path.exists('proxies.txt'):
        print(Fore.RED + "Không tìm thấy file proxies.txt!")
        return

    try:
        with open('proxies.txt', 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(Fore.RED + f"Lỗi đọc file proxies.txt: {e}")
        return

    if not proxies:
        print(Fore.RED + "Danh sách proxy trống!")
        return

    # Lọc các proxy hoạt động
    working_proxies = []
    print(Fore.CYAN + "Đang kiểm tra các proxy...")
    for p in proxies:
        if validate_proxy(p):
            working_proxies.append(p)

    if not working_proxies:
        print(Fore.RED + "Không có proxy nào hoạt động!")
        return

    print(Fore.CYAN + f"Đã tìm thấy {len(working_proxies)} proxy hoạt động.")

    for p in working_proxies:
        while threading.active_count() > N_THREADS:
            time.sleep(1)
        thread = threading.Thread(target=checker, args=(p,), daemon=True)
        threads.append(thread)
        thread.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "Đang dừng tool...")
        stop_event.set()
        for t in threads:
            t.join(timeout=1)  # Chờ tối đa 1 giây cho mỗi luồng
        print(Fore.GREEN + "Tool đã dừng hoàn toàn!")

if __name__ == "__main__":
    start()
