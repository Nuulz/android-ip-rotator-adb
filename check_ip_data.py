import subprocess
import time
import requests
import sys

# ---------------- CONFIG ----------------

# Path to adb binary (user must change this)
ADB_PATH = r"PATH_TO_YOUR_ADB\adb.exe"

# Timings (tweak if needed)
AIRPLANE_WAIT = 30      # seconds airplane mode stays ON
POST_WAIT = 5           # wait after reconnect
MAX_ATTEMPTS = 3
IP_TIMEOUT = 5

# MODE:
# "A" = airplane only
# "B" = airplane + mobile data toggle
MODE = "B"

# ----------------------------------------


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def adb(cmd):
    """
    Run adb command using full path.
    """
    result = subprocess.run(
        f'"{ADB_PATH}" {cmd}',
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        log(f"ADB warning: {result.stderr.strip()}")

    return result.stdout.strip()


def get_public_ip():
    """
    Get current public IPv4 from external services.
    """
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip"
    ]

    for url in services:
        try:
            r = requests.get(url, timeout=IP_TIMEOUT)
            if r.status_code == 200:
                return r.text.strip()
        except:
            pass

    return None


def rotation_cycle():
    ip_before = get_public_ip()

    if not ip_before:
        log("No internet at start. Check USB tethering.")
        return False

    log(f"Current IP: {ip_before}")

    if MODE == "A":
        log("Mode A → airplane only")

        adb("shell settings put global airplane_mode_on 1")
        time.sleep(AIRPLANE_WAIT)
        adb("shell settings put global airplane_mode_on 0")

    elif MODE == "B":
        log("Mode B → airplane → data OFF → airplane OFF → data ON")

        adb("shell settings put global airplane_mode_on 1")
        time.sleep(2)

        adb("shell svc data disable")
        time.sleep(AIRPLANE_WAIT)

        adb("shell settings put global airplane_mode_on 0")
        time.sleep(2)

        adb("shell svc data enable")

    else:
        log("Invalid MODE selected.")
        return False

    log("Waiting for network to come back...")
    time.sleep(POST_WAIT)

    ip_after = get_public_ip()

    if not ip_after:
        log("Internet did not come back.")
        return False

    log(f"New IP: {ip_after}")

    if ip_after != ip_before:
        log("IP rotated successfully.")
        return True
    else:
        log("IP did not change.")
        return False


if __name__ == "__main__":
    log(f"=== EXPERIMENTAL IP ROTATOR (MODE {MODE}) ===")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        log(f"--- Attempt {attempt} ---")

        if rotation_cycle():
            sys.exit(0)

        time.sleep(10)

    log("All attempts exhausted.")
    sys.exit(1)
