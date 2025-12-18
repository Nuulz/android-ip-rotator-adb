import sys
import os
import time
import json
import shutil

from core.rotator import rotation_cycle, log
from core.logger import start_radio_capture, stop_radio_capture
from core.analyzer import scan_log_for_markers
from core.events import parse_events, export_json, export_csv
from core.index import register_run, load_index, save_index
from datetime import datetime

LOGS_DIR = "logs"
CONFIG_DIR = os.path.join(LOGS_DIR, "configs")
RUNS_DIR = os.path.join(LOGS_DIR, "runs")

INDEX_FILE = os.path.join(RUNS_DIR, "index.json")

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_config():
    if not os.path.isfile(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def delete_run():
    index = list_runs()
    if not index:
        return

    choice = input("Select run to delete (or ENTER to cancel): ").strip()
    if not choice:
        return

    try:
        idx = int(choice) - 1
        run = index[idx]
    except:
        print("[ERROR] Invalid selection.")
        return

    print(f"\nYou are about to delete:")
    print(f" - Run: {run['run_id']}")
    print(f" - Path: {run['log_path']}")

    confirm = input("Type DELETE to confirm: ").strip()
    if confirm != "DELETE":
        print("[INFO] Cancelled.")
        return

    run_dir = os.path.dirname(run["log_path"])

    shutil.rmtree(run_dir, ignore_errors=True)

    index.pop(idx)
    save_index(index)

    print("[INFO] Run deleted safely.")

def delete_all_runs():
    index = load_index()
    if not index:
        print("[INFO] No runs registered in index.")
        #It happens to me, hahahaha.
        print("[INFO] Note: Only runs created via option 3 are tracked.")
        return

    print(f"[WARN] This will delete {len(index)} runs.")

    confirm = input("Type DELETE ALL to confirm: ").strip()
    if confirm != "DELETE ALL":
        print("[INFO] Cancelled.")
        return

    for entry in index:
        run_dir = os.path.dirname(entry["log_path"])
        shutil.rmtree(run_dir, ignore_errors=True)

    save_index([])

    print("[INFO] All runs deleted.")

def clean_logs_menu():
    while True:
        print("\nClean logs:")
        print("1) Delete a specific run")
        print("2) Delete all runs")
        print("3) Back")

        choice = input("> ").strip()

        if choice == "1":
            delete_run()
        elif choice == "2":
            delete_all_runs()
        elif choice == "3":
            return
        else:
            print("Invalid option.")


def ensure_directories():
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(RUNS_DIR, exist_ok=True)

def create_run_dir():
    run_id = datetime.now().strftime("run_%Y-%m-%d_%H-%M-%S")
    run_path = os.path.join(RUNS_DIR, run_id)
    os.makedirs(run_path, exist_ok=True)
    return run_path


def list_runs():
    index = load_index()
    if not index:
        print("[INFO] No runs found.")
        return []

    for i, entry in enumerate(index, 1):
        status = "IP changed" if entry["ip_changed"] else "IP unchanged"
        print(f"{i}) {entry['run_id']} | {entry['timestamp']} | {status}")

    return index

def select_log_file():
    logs = []

    # Buscar logs en runs/
    if os.path.isdir(RUNS_DIR):
        for run in sorted(os.listdir(RUNS_DIR), reverse=True):
            run_path = os.path.join(RUNS_DIR, run)
            log_path = os.path.join(run_path, "radio.log")

            if os.path.isfile(log_path):
                logs.append(log_path)

    if not logs:
        print("[WARN] No radio logs found.")
        return None

    print("\nAvailable logs:")
    for i, path in enumerate(logs, 1):
        print(f"{i}) {path}")

    choice = input("Select log number (or ENTER for latest): ").strip()

    if choice == "":
        return logs[0]

    try:
        idx = int(choice) - 1
        return logs[idx]
    except:
        print("[ERROR] Invalid selection.")
        return None

def ask_adb_path():
    config = load_config()

    if "adb_path" in config and os.path.isfile(config["adb_path"]):
        print(f"[INFO] Using saved adb path: {config['adb_path']}")
        change = input("Change adb path? (y/N): ").strip().lower()

        if change != "y":
            return config["adb_path"]

    adb_dir = input("Path to adb directory (e.g. D:\\android\\platform-tools): ").strip()
    adb_path = os.path.join(adb_dir, "adb.exe")

    if not os.path.isfile(adb_path):
        print(f"[ERROR] adb.exe not found in: {adb_dir}")
        sys.exit(1)

    config["adb_path"] = adb_path
    save_config(config)

    print("[INFO] adb path saved.")

    return adb_path


def ask_rotation_params():
    mode = input("Mode (A = airplane / B = airplane+data): ").strip().upper()
    airplane_wait = int(input("Airplane wait (seconds) [30]: ") or 30)
    post_wait = int(input("Post reconnect wait (seconds) [5]: ") or 5)
    ip_timeout = int(input("IP request timeout (seconds) [5]: ") or 5)
    max_attempts = int(input("Max attempts [3]: ") or 3)

    return mode, airplane_wait, post_wait, ip_timeout, max_attempts


def run_rotation(adb_path):
    mode, airplane_wait, post_wait, ip_timeout, max_attempts = ask_rotation_params()

    for attempt in range(1, max_attempts + 1):
        log(f"--- Attempt {attempt} ---")

        if rotation_cycle(
            adb_path=adb_path,
            mode=mode,
            airplane_wait=airplane_wait,
            post_wait=post_wait,
            ip_timeout=ip_timeout
        ):
            log("IP rotated successfully.")
            return True, mode, max_attempts

    log("All attempts exhausted.")
    return False, mode, max_attempts



def run_log_capture(adb_path):
    duration = int(input("Log capture duration (seconds) [30]: ") or 30)
    filename = f"radio_debug_{int(time.time())}.log"

    path = capture_radio_logs(
        adb_path=adb_path,
        filename=filename,
        duration=duration
    )

    print(f"[INFO] Logs saved to: {path}")


def run_log_capture_and_analyze(adb_path):
    duration = int(input("Log capture duration (seconds) [30]: ") or 30)
    filename = f"radio_analysis_{int(time.time())}.log"

    path = capture_radio_logs(
        adb_path=adb_path,
        filename=filename,
        duration=duration
    )

    print(f"[INFO] Logs saved to: {path}")
    print("[INFO] Analyzing log...")

    results = scan_log_for_markers(path)

    print("\nAnalysis summary:")
    for key, value in results.items():
        status = "YES" if value else "NO"
        print(f" - {key}: {status}")


def main():
    ensure_directories()
    print("=== Android IP Rotator (Experimental) ===")
    adb_path = ask_adb_path()

    while True:
        print("\nSelect an option:")
        print("1) Run IP rotation experiment")
        print("2) Capture radio debug logs")
        print("3) Capture logs + run experiment")
        print("4) Analyze logs")
        print("5) Extract events from log")
        print("6) Clean logs (safe)")
        print("7) Exit")

        choice = input("> ").strip()

        if choice == "1":
            run_rotation(adb_path)

        elif choice == "2":
            run_log_capture(adb_path)

        elif choice == "3":
            print("[INFO] Starting radio log capture...")

            run_dir = create_run_dir()
            run_id = os.path.basename(run_dir)
            logfile = os.path.join(run_dir, "radio.log")

            log_proc = start_radio_capture(adb_path, logfile)

            try:
                ip_changed, mode, attempts = run_rotation(adb_path)
            finally:
                stop_radio_capture(log_proc)
                print(f"[INFO] Logs saved to: {logfile}")

            events = parse_events(logfile)

            export_json(events, os.path.join(run_dir, "events.json"))
            export_csv(events, os.path.join(run_dir, "events.csv"))

            register_run(
                run_id=run_id,
                mode=mode,
                attempts=attempts,
                ip_changed=ip_changed,
                events_detected=len(events),
                log_path=logfile
            )

            print("[INFO] Run registered in index.")


        elif choice == "4":
            log_file = select_log_file()

            if not log_file:
                continue

            print(f"[INFO] Analyzing log: {log_file}")

            results = scan_log_for_markers(log_file)

            print("\nAnalysis summary:")
            for key, value in results.items():
                status = "YES" if value else "NO"
                print(f" - {key}: {status}")

        elif choice == "5":
            log_file = select_log_file()
            if not log_file:
                continue

            print(f"[INFO] Analyzing log: {log_file}")

            events = parse_events(log_file)

            base = log_file.replace(".log", "")
            export_json(events, base + ".json")
            export_csv(events, base + ".csv")

            print(f"[INFO] Extracted {len(events)} events")
            print(f"[INFO] JSON: {base}.json")
            print(f"[INFO] CSV: {base}.csv")

            print("\nDetected event types:")
            for e in sorted(set(ev["event"] for ev in events)):
                print(f" - {e}")

        elif choice == "6":
            clean_logs_menu()

        elif choice == "7":
            print("Exiting.")
            sys.exit(0)

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()