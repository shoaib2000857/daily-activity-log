import requests
import os
from datetime import date
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # loads variables from .env into environment

WAKATIME_API_KEY = os.getenv('WAKATIME_API_KEY')
if not WAKATIME_API_KEY:
    print("ERROR: Please set the WAKATIME_API_KEY environment variable.")
    exit(1)

MINUTES_PER_COMMIT = 15
default_manual = 60
inp = input(f"Enter manual time spent today in minutes [default: {default_manual}]: ").strip()
MANUAL_TIME = int(inp) if inp.isdigit() else default_manual

# === SETUP PATHS ===
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / 'logs'
TODAY = date.today().isoformat()
LOG_FILE = LOGS_DIR / f"{TODAY}.md"

# === FETCH WAKATIME DATA ===
def fetch_wakatime_data():
    url = f"https://wakatime.com/api/v1/users/current/summaries?start={TODAY}&end={TODAY}"
    headers = {'Authorization': f'Bearer {WAKATIME_API_KEY}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        total = data['data'][0]['grand_total']['total_seconds'] / 60  # in minutes
        return round(total)
    else:
        print("Error fetching WakaTime data:", response.text)
        return 0

# === LOG ACTIVITY ===
def write_log(coding_time, manual_time):
    LOGS_DIR.mkdir(exist_ok=True)
    total_time = coding_time + manual_time

    with open(LOG_FILE, 'w') as f:
        f.write(f"# Daily Activity Log - {TODAY}\n\n")
        f.write(f"**Coding (WakaTime):** {coding_time} minutes\n")
        f.write(f"**Manual work (Research/Hardware):** {manual_time} minutes\n")
        f.write(f"**Total Time:** {total_time} minutes\n\n")
        f.write("### Activity Blocks\n")

    return total_time

# === COMMIT CHUNKS ===
def commit_chunks(total_minutes):
    chunk_count = total_minutes // MINUTES_PER_COMMIT

    for i in range(chunk_count):
        with open(LOG_FILE, 'a') as f:
            f.write(f"- Activity block #{i+1}\n")

        subprocess.run(['git', 'add', '.'], cwd=BASE_DIR, shell=True)
        subprocess.run(['git', 'commit', '-m', f"Log block {i+1} for {TODAY}"], cwd=BASE_DIR, shell=True)

    subprocess.run(['git', 'push'], cwd=BASE_DIR, shell=True)

# === MAIN ===
if __name__ == "__main__":
    wakatime_minutes = fetch_wakatime_data()
    total = write_log(wakatime_minutes, MANUAL_TIME)
    commit_chunks(total)
