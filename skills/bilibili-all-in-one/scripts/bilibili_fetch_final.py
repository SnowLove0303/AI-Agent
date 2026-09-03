#!/usr/bin/env python3
"""Bilibili fetcher - uses video-info API with known BV IDs"""
import requests
import json
import time
import os
import subprocess

# Load cookies
STATE_FILE = r"D:\APP\AI app\deepseek\.agents\skills\bilibili-all-in-one\.runtime\bilibili-cookie-state.json"

def load_cookies():
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        return state.get("cookie", "")
    except:
        return ""

COOKIES = load_cookies()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
    "Cookie": COOKIES
}

# Known latest BV IDs for each UP主
# Update these BV IDs when new videos are released
KNOWN_VIDEOS = [
    {"name": "Juya", "bv": "BV1mDtL6hE4x"},
    {"name": "Heiya", "bv": "BV1dxt36wEbp"},
]

PYTHON = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
OUTPUT_DIR = r"F:\Workspace\Deepseek Harness\2026825\daily_reports"

def get_video_info(bvid):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        if data.get("code") == 0:
            return data.get("data")
    except Exception as e:
        print(f"  Error: {e}")
    return None

def get_audio_url(bvid, cid):
    url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&fnval=16&qn=64"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        if data.get("code") == 0:
            audio = data.get("data", {}).get("dash", {}).get("audio", [])
            if audio:
                return audio[0].get("baseUrl")
    except:
        pass
    return None

def download_audio(url, path):
    try:
        r = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return True
    except:
        return False

def transcribe(audio_path, transcript_path):
    script = f'''
from faster_whisper import WhisperModel
model = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = model.transcribe(r"{audio_path}", language="zh")
transcript = []
for seg in segments:
    transcript.append(f"[{{seg.start:.1f}}s - {{seg.end:.1f}}s] {{seg.text}}")
with open(r"{transcript_path}", "w", encoding="utf-8") as f:
    f.write("\\n".join(transcript))
print(f"{{len(transcript)}} segments")
'''
    script_file = os.path.join(os.path.dirname(transcript_path), "_temp.py")
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script)
    
    result = subprocess.run([PYTHON, script_file], capture_output=True, text=True)
    os.remove(script_file)
    
    if result.returncode == 0:
        print(f"  {result.stdout.strip()}")
    return os.path.exists(transcript_path)

def generate_report(name, bvid, title, date, duration, plays, transcript):
    report_path = os.path.join(OUTPUT_DIR, f"{name}_{date}.md")
    
    report = f"""# AI Report {date}

**Source**: {name} - {bvid}
**Duration**: {duration}min | **Plays**: {plays}

---

## Transcript

{transcript}

---

*Generated: {time.strftime('%Y-%m-%d %H:%M')}*
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    return report_path

def main():
    today = time.strftime("%Y-%m-%d")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"=== Bilibili Fetcher - {today} ===")
    print(f"Cookies: {'Loaded' if COOKIES else 'None'}")
    
    for video in KNOWN_VIDEOS:
        name = video["name"]
        bvid = video["bv"]
        
        print(f"\n[{name}] BV={bvid}")
        
        # Get video info
        time.sleep(3)
        info = get_video_info(bvid)
        if not info:
            print("  Cannot get info")
            continue
        
        title = info.get("title", "")
        pub_date = time.strftime("%Y-%m-%d", time.localtime(info.get("pubdate", 0)))
        duration = round(info.get("duration", 0) / 60, 1)
        plays = info.get("stat", {}).get("view", 0)
        cid = info.get("cid")
        
        is_today = pub_date == today
        print(f"  {'[TODAY]' if is_today else '[LATEST]'} {title[:60]}")
        print(f"  Date: {pub_date} | Duration: {duration}min | Views: {plays}")
        
        # Get audio URL
        time.sleep(2)
        audio_url = get_audio_url(bvid, cid)
        if not audio_url:
            print("  No audio URL")
            continue
        
        # Download
        audio_file = os.path.join(OUTPUT_DIR, f"{bvid}.m4a")
        print("  Downloading...")
        if not download_audio(audio_url, audio_file):
            print("  Download failed")
            continue
        
        # Transcribe
        transcript_file = os.path.join(OUTPUT_DIR, f"transcript_{bvid}.txt")
        print("  Transcribing...")
        if transcribe(audio_file, transcript_file):
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcript = f.read()
            
            # Generate report
            report_path = generate_report(name, bvid, title, pub_date, duration, plays, transcript)
            print(f"  Saved: {report_path}")
        
        # Cleanup
        if os.path.exists(audio_file):
            os.remove(audio_file)
    
    print("\n=== Done ===")

if __name__ == "__main__":
    main()
