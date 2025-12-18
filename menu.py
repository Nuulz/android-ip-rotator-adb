import sys
import os
import time

from core.rotator import rotation_cycle, log
from core.logger import start_radio_capture, stop_radio_capture
from core.analyzer import scan_log_for_markers

def select_log_file():
    logs_dir = "logs"

    if not os.path.isdir(logs_dir):
        print("[ERROR] No logs directory found.")
        return None

    logs = sorted(
        [f for f in os.listdir(logs_dir) if f.endswith(".log")],
        key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)),
        reverse=True
    )

    if not logs:
        print("[ERROR] No log files found.")
        return None

    print("\nAvailable log files:")
    for idx, log_file in enumerate(logs, 1):
        print(f"{idx}) {log_file}")

    print("0) Use latest log")

    choice = input("> ").strip()

    if choice == "0" or choice == "":
        return os.path.join(logs_dir, logs[0])

    try:
        index = int(choice) - 1
        return os.path.join(logs_dir, logs[index])
    except (ValueError, IndexError):
        print("[ERROR] Invalid selection.")
        return None

def ask_adb_path():
    adb_dir = input("Path to adb directory (e.g. D:\\android\\platform-tools): ").strip()
    adb_path = os.path.join(adb_dir, "adb.exe")

    if not os.path.isfile(adb_path):
        print(f"[ERROR] adb.exe not found in: {adb_dir}")
        sys.exit(1)

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
            return

    log("All attempts exhausted.")


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
    print("=== Android IP Rotator (Experimental) ===")
    adb_path = ask_adb_path()

    while True:
        print("\nSelect an option:")
        print("1) Run IP rotation experiment")
        print("2) Capture radio debug logs")
        print("3) Capture logs + run experiment")
        print("4) Analyze logs")
        print("5) Exit")

        choice = input("> ").strip()

        if choice == "1":
            run_rotation(adb_path)

        elif choice == "2":
            run_log_capture(adb_path)

        elif choice == "3":
            print("[INFO] Starting radio log capture...")

            logfile = f"logs/radio_experiment_{int(time.time())}.log"

            log_proc = start_radio_capture(adb_path, logfile)

            try:
                run_rotation(adb_path)
            finally:
                stop_radio_capture(log_proc)
                print(f"[INFO] Logs saved to: {logfile}")

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
            print("Exiting.")
            sys.exit(0)

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()