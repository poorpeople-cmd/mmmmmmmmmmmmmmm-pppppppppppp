import os
import time
import subprocess
import urllib.parse
import traceback
import requests
from datetime import datetime, timezone, timedelta
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# ==========================================
# ⚙️ MAIN SETTINGS (DYNAMIC FROM GITHUB)
# ==========================================
DEFAULT_URL = "https://dadocric.st/player.php?id=willowextra"
TARGET_WEBSITE = os.environ.get('TARGET_URL', DEFAULT_URL)

# --- NAYA LOGIC: Number se Stream Key nikalna ---
STREAM_ID = str(os.environ.get('STREAM_ID', '1'))

MULTI_KEYS = {
    '1': os.environ.get('STREAM_KEY', '14136719122027_13152308497003_hnlk6em2e4'), # Default Key
    # '1': '13792808935019_12476172012139_mstifuzoo4',
    '2': '15255038074475_15283122080363_ai5qqp2we4', # 👈 Apni Stream 2 ki key yahan dalein
    '3': '15255045480043_15283135842923_tldl4bhmii',  # 👈 Apni Stream 3 ki key yahan dalein
    '4': '14136778563179_13152426265195_c5quhoj2vm'
}

STREAM_KEY = MULTI_KEYS.get(STREAM_ID, MULTI_KEYS['1'])
RTMP_URL = f"rtmp://vsu.okcdn.ru/input/{STREAM_KEY}"
# ------------------------------------------------

PROXY_IP = os.environ.get('PROXY_IP', '31.59.20.176')
PROXY_PORT = os.environ.get('PROXY_PORT', '6754')
PROXY_USER = os.environ.get('PROXY_USER', 'cjasfidu')
PROXY_PASS = os.environ.get('PROXY_PASS', 'qhnyvm0qpf6p')
PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_IP}:{PROXY_PORT}"

# --- MANUAL MODE INPUTS ---
MANUAL_M3U8 = os.environ.get('MANUAL_M3U8', '').strip()
MANUAL_REFERER = os.environ.get('MANUAL_REFERER', '').strip()
MANUAL_ORIGIN = os.environ.get('MANUAL_ORIGIN', '').strip()

# --- CASE 2: RAW COMMAND INPUT ---
MANUAL_FFMPEG_CMD = os.environ.get('MANUAL_FFMPEG_CMD', '').strip()

DEFAULT_SLEEP = 45 * 60 
PKT = timezone(timedelta(hours=5))
# ==========================================

def trigger_next_run():
    print("\n" + "="*50)
    print(" ⏰ AUTO-RESTART TRIGGER ACTIVATED ⏰")
    print("="*50)
    print("[🔄] 5 Ghante 45 Minute poore ho gaye hain! Naya Bot chala raha hoon...")
    
    token = os.environ.get('GH_PAT')
    repo = os.environ.get('GITHUB_REPOSITORY') 
    branch = os.environ.get('GITHUB_REF_NAME', 'main')
    
    if not token or not repo:
        print("[❌] GH_PAT ya Repo Name nahi mila! Auto-Restart Fail ho gaya.")
        return

    url = f"https://api.github.com/repos/{repo}/actions/workflows/stream.yml/dispatches"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}"
    }
    
    data = {
        "ref": branch,
        "inputs": {
            "stream_id": STREAM_ID, # 👈 NAYA LOGIC: Auto-restart mein same Server ID dobara bhejega
            "target_url": TARGET_WEBSITE,
            "stream_key": STREAM_KEY,
            "proxy_ip": PROXY_IP,
            "proxy_port": PROXY_PORT,
            "proxy_user": PROXY_USER,
            "proxy_pass": PROXY_PASS,
            "manual_m3u8": MANUAL_M3U8,
            "manual_referer": MANUAL_REFERER,
            "manual_origin": MANUAL_ORIGIN,
            "manual_ffmpeg_cmd": MANUAL_FFMPEG_CMD
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 204:
            print(f"[✅] SUCCESS! Nayi 'stream.yml' (Server {STREAM_ID}) background mein start ho gayi hai!")
        else:
            print(f"[❌] FAILED to start new bot. Status: {response.status_code}")
    except Exception as e:
        print(f"[💥] API Error: {e}")

def get_link_with_headers():
    print(f"\n========================================")
    print(f"[🔍] [STEP 1] Target URL Set: {TARGET_WEBSITE}")
    print(f"[🔍] [STEP 2] Proxy Set for Link Fetching: {PROXY_URL.split('@')[-1]}")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--autoplay-policy=no-user-gesture-required')
    options.add_argument('--mute-audio')
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

    seleniumwire_options = {
        'proxy': {'http': PROXY_URL, 'https': PROXY_URL, 'no_proxy': 'localhost,127.0.0.1'},
        'disable_encoding': True, 
        'connection_keep_alive': True
    }

    driver = None
    data = None

    try:
        print(f"[⚙️] [STEP 3] Chrome Browser start ho raha hai Proxy ke sath...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), seleniumwire_options=seleniumwire_options, options=options)
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"[🌐] [STEP 5] Website open kar raha hoon...")
        driver.get(TARGET_WEBSITE)
        
        print("[⏳] [STEP 6] Website load ho gayi! 5 Seconds wait...") 
        for i in range(5, 0, -1):
            time.sleep(1)
            
        print("[✅] [STEP 7] Scanning network requests for .m3u8 token...")

        for request in driver.requests:
            if request.response:
                if ".m3u8" in request.url:
                    headers = request.headers
                    data = {
                        "url": request.url,
                        "ua": headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
                        "cookie": headers.get('Cookie', ''),
                        "referer": headers.get('Referer', TARGET_WEBSITE),
                        "origin": ""
                    }
                    print(f"\n🎉 [BINGO] Cloudflare Bypassed! Link Mil Gaya!")
                    break
                    
        if not data:
            print("\n[🚨] WARNING: .m3u8 link nahi mila! WAF ne block kiya ya wait time kam tha.")
            
    except Exception as e:
        print(f"\n[💥] PYTHON SCRIPT ERROR (Browser Crash):")
        print(traceback.format_exc())
    finally:
        if driver: 
            print("[🧹] [STEP 8] Chrome Browser band kiya ja raha hai...")
            driver.quit()
    
    return data

def calculate_sleep_time(url):
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        expiry_ts = None
        
        if 'expires' in params: expiry_ts = int(params['expires'][0])
        elif 'e' in params: expiry_ts = int(params['e'][0])
            
        if expiry_ts:
            expiry_dt = datetime.fromtimestamp(expiry_ts, PKT)
            wake_up_dt = expiry_dt - timedelta(minutes=5)
            now_dt = datetime.now(PKT)
            seconds = (wake_up_dt - now_dt).total_seconds()
            
            print(f"[⏰] Asli Link Expiry Time: {expiry_dt.strftime('%I:%M %p')} PKT")
            print(f"[🛠️] Pre-Fetch Time: Bot {wake_up_dt.strftime('%I:%M %p')} par uthega.")
            
            if seconds > 0: return seconds
            else: return 60
    except Exception:
        pass
    return DEFAULT_SLEEP

#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
def start_stream(data):
    headers_cmd = f"User-Agent: {data['ua']}\r\nReferer: {data['referer']}\r\nCookie: {data['cookie']}"
    if data.get('origin'):
        headers_cmd += f"\r\nOrigin: {data['origin']}"
    
    print("\n[🎬] [STEP 9] FFmpeg Command tayyar ki ja rahi hai (360p ULTRA-LOW BANDWIDTH)...")
    cmd = [
        "ffmpeg", "-re",
        "-loglevel", "error", 
        "-fflags", "+genpts",  
        "-headers", headers_cmd,
        "-i", data['url'],
        "-c:v", "libx264", "-preset", "ultrafast",
        "-b:v", "300k", "-maxrate", "400k", "-bufsize", "800k", 
        "-vf", "scale=640:360", "-r", "20",                     
        "-c:a", "aac", "-b:a", "32k", "-ar", "44100",           
        "-async", "1",         
        "-f", "flv", RTMP_URL
    ]
    print("[⚙️] [STEP 10] FFmpeg Stream Launch ho rahi hai! (Slow Internet Optimized)")
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL)

def main():
    print("========================================")
    print("   🚀 ULTIMATE ALL-IN-ONE STREAMER")
    print(f"   📡 SELECTED SERVER ID: {STREAM_ID}")
    print("========================================")
    
    start_time = time.time()
    RESTART_TIME_LIMIT = (5 * 60 * 60) + (45 * 60) # 5h 45m
    end_time = start_time + (6 * 60 * 60)
    
    # ====================================================
    # 🔥 CASE 2: RAW FFMPEG COMMAND OVERRIDE LOGIC
    # ====================================================
    if MANUAL_FFMPEG_CMD:
        print("\n[🎯] ⚡ RAW FFMPEG COMMAND OVERRIDE ACTIVATED ⚡")
        print("Bot apni link-finding logic band kar raha hai aur direct aapki command chala raha hai...")
        
        next_run_triggered = False
        while time.time() < end_time:
            if (time.time() - start_time) > RESTART_TIME_LIMIT and not next_run_triggered:
                trigger_next_run()
                next_run_triggered = True

            print(f"\n[🎬] Executing Full Command: \n{MANUAL_FFMPEG_CMD[:150]}... (truncated for display)")
            
            try:
                current_process = subprocess.Popen(MANUAL_FFMPEG_CMD, shell=True)
                current_process.wait() 
            except Exception as e:
                print(f"[💥] Command Error: {e}")
                
            print("\n[⚠️] Command rukk gayi ya stream crash ho gayi. 10 second baad dobara try kar raha hoon...")
            time.sleep(10)
            
        return 
    # ====================================================

    current_process = None
    next_run_triggered = False
    is_manual_mode = bool(MANUAL_M3U8)

    if is_manual_mode:
        print("\n[🎯] ⚡ MANUAL M3U8 LINK ACTIVATED ⚡")
        data = {
            "url": MANUAL_M3U8,
            "referer": MANUAL_REFERER,
            "origin": MANUAL_ORIGIN,
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "cookie": ""
        }
    else:
        data = get_link_with_headers()

    while time.time() < end_time:
        try:
            if not data:
                print("\n[🔄] Link lene ja raha hoon...")
                data = get_link_with_headers()
                if not data:
                    print("\n[❌] Link nahi mila. 1 minute baad dobara koshish hogi...")
                    time.sleep(60)
                    continue

            if current_process: current_process.terminate()
            current_process = start_stream(data)
            print("\n[🚀] SUCCESS! Video feed OK.ru par live hai!")
            
            if is_manual_mode:
                sleep_seconds = 10 * 60 * 60
            else:
                sleep_seconds = calculate_sleep_time(data['url'])
                print(f"[zzz] AUTO MODE: Bot {int(sleep_seconds/60)} mins rest karega...")
            
            waited = 0
            crashed = False
            
            while waited < sleep_seconds:
                time.sleep(10)
                waited += 10
                
                if (time.time() - start_time) > RESTART_TIME_LIMIT and not next_run_triggered:
                    trigger_next_run()
                    next_run_triggered = True 
                    
                if current_process.poll() is not None:
                    exit_code = current_process.poll()
                    print(f"\n[⚠️] FFmpeg Stream Crashed! (Exit Code: {exit_code})")
                    crashed = True
                    break 
            
            if not is_manual_mode and not crashed:
                print("\n[🕵️‍♂️] PRE-FETCH MODE: Background mein naya link la raha hoon...")
                new_data = get_link_with_headers()
                if new_data:
                    print("\n[⚡] NAYA LINK READY! Millisecond swap kar raha hoon...")
                    data = new_data 
                else:
                    print("\n[⚠️] Pre-fetch fail! Purani stream ko natural crash hone tak chalne do...")
                    current_process.wait() 
                    data = None 
            elif crashed and not is_manual_mode:
                data = None 

        except Exception:
            print(f"\n[💥] MAIN LOOP ERROR:")
            print(traceback.format_exc())
            time.sleep(60)

if __name__ == "__main__":
    main()

