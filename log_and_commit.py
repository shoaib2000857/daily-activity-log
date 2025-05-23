import requests
import os
import re
from datetime import date
import subprocess
from pathlib import Path
import base64

from dotenv import load_dotenv

load_dotenv()  # Load variables from .env into environment

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
    encoded_key = base64.b64encode(WAKATIME_API_KEY.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_key}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        total = data['data'][0]['grand_total']['total_seconds'] / 60  # in minutes
        return round(total)
    else:
        print("Error fetching WakaTime data:", response.status_code, response.text)
        return 0

# === READ EXISTING LOG DATA ===
def read_existing_data():
    if not LOG_FILE.exists():
        return 0, 0  # manual time, activity blocks

    manual_time = 0
    block_count = 0

    with open(LOG_FILE) as f:
        for line in f:
            if "Manual work" in line:
                match = re.search(r"(\d+)\s+minutes", line)
                if match:
                    manual_time = int(match.group(1))
            elif line.strip().startswith("- Activity block"):
                block_count += 1

    return manual_time, block_count

# === WRITE LOG ===
def write_log(coding_time, manual_time, previous_manual, existing_blocks):
    LOGS_DIR.mkdir(exist_ok=True)
    total_manual = previous_manual + manual_time
    total_time = coding_time + total_manual

    with open(LOG_FILE, 'w') as f:
        f.write(f"# Daily Activity Log - {TODAY}\n\n")
        f.write(f"**Coding (WakaTime):** {coding_time} minutes\n")
        f.write(f"**Manual work (Research/Hardware):** {total_manual} minutes\n")
        f.write(f"**Total Time:** {total_time} minutes\n\n")
        f.write("### Activity Blocks\n")
        for i in range(existing_blocks):
            f.write(f"- Activity block #{i+1}\n")

    return total_time, total_manual, existing_blocks

# === COMMIT NEW CHUNKS ===
def commit_chunks(total_minutes, existing_blocks):
    chunk_count = total_minutes // MINUTES_PER_COMMIT
    new_blocks = chunk_count - existing_blocks

    for i in range(existing_blocks, chunk_count):
        with open(LOG_FILE, 'a') as f:
            f.write(f"- Activity block #{i+1}\n")

        # Run git commands WITHOUT shell=True since you're passing a list
        subprocess.run(['git', 'add', '.'], cwd=BASE_DIR)
        subprocess.run(['git', 'commit', '-m', f"Log block {i+1} for {TODAY}"], cwd=BASE_DIR)

    if new_blocks > 0:
        subprocess.run(['git', 'push'], cwd=BASE_DIR)


# === MAIN ===
if __name__ == "__main__":
    wakatime_minutes = fetch_wakatime_data()
    prev_manual, existing_blocks = read_existing_data()
    total_time, total_manual, existing_blocks = write_log(wakatime_minutes, MANUAL_TIME, prev_manual, existing_blocks)
    commit_chunks(total_time, existing_blocks)
