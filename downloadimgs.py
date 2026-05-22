import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

API_STATE   = "https://api.waterfallhunt.com/api/state"
API_BASE    = "https://api.waterfallhunt.com"
OUTPUT_DIR  = "cam1_images"
MAX_WORKERS = 20
TIMEOUT     = 15

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer":    "https://waterfallhunt.com/",
    "Origin":     "https://waterfallhunt.com",
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Fetching frame list from API...")
state = requests.get(API_STATE, headers=HEADERS, timeout=15).json()
frames = state.get("cam1_frames", [])
print(f"Found {len(frames)} cam1 frames  ({frames[0]['id']} → {frames[-1]['id']})\n")

def download(frame):
    ts  = frame["id"]
    url = API_BASE + frame["preview_url"]
    out = os.path.join(OUTPUT_DIR, f"{ts}.webp")
    if os.path.exists(out):
        return ts, "skip"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200:
            with open(out, "wb") as f:
                f.write(r.content)
            return ts, "ok"
        return ts, f"skip ({r.status_code})"
    except Exception as e:
        return ts, f"err ({e})"

downloaded = skipped = errors = 0

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(download, f): f for f in frames}
    done = 0
    for future in as_completed(futures):
        ts, status = future.result()
        done += 1
        if status == "ok":
            downloaded += 1
            print(f"[{done}/{len(frames)}] SAVED  {ts}")
        elif status == "skip":
            skipped += 1
        elif not status.startswith("skip"):
            errors += 1
            print(f"[{done}/{len(frames)}] ERROR  {ts}: {status}")
        if done % 100 == 0:
            print(f"  ... {done}/{len(frames)} done, {downloaded} saved")

print(f"\nDone. {downloaded} downloaded, {skipped} already existed, {errors} errors.")
print(f"Images saved to: {os.path.abspath(OUTPUT_DIR)}")
