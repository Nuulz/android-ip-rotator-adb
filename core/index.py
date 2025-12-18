import os
import json
from datetime import datetime


RUNS_DIR = os.path.join("logs", "runs")
INDEX_FILE = os.path.join(RUNS_DIR, "index.json")


def load_index():
    if not os.path.isfile(INDEX_FILE):
        return []
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_index(index):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def register_run(
    run_id,
    mode,
    attempts,
    ip_changed,
    events_detected,
    log_path
):
    index = load_index()

    entry = {
        "run_id": run_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "attempts": attempts,
        "ip_changed": ip_changed,
        "events_detected": events_detected,
        "log_path": log_path
    }

    index.append(entry)
    save_index(index)
