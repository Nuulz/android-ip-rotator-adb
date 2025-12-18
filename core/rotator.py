import subprocess
import time
import requests


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def adb(adb_path, cmd):
    result = subprocess.run(
        f'"{adb_path}" {cmd}',
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        log(f"ADB warning: {result.stderr.strip()}")

    return result.stdout.strip()


def get_public_ip(timeout):
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip"
    ]

    for url in services:
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.text.strip()
        except:
            pass

    return None


def rotation_cycle(
    adb_path,
    mode,
    airplane_wait,
    post_wait,
    ip_timeout
):
    ip_before = get_public_ip(ip_timeout)

    if not ip_before:
        log("No internet at start.")
        return False

    log(f"Current IP: {ip_before}")

    if mode == "A":
        log("Mode A → airplane only")

        adb(adb_path, "shell settings put global airplane_mode_on 1")
        time.sleep(airplane_wait)
        adb(adb_path, "shell settings put global airplane_mode_on 0")

    elif mode == "B":
        log("Mode B → airplane → data OFF → airplane OFF → data ON")

        adb(adb_path, "shell settings put global airplane_mode_on 1")
        time.sleep(2)

        adb(adb_path, "shell svc data disable")
        time.sleep(airplane_wait)

        adb(adb_path, "shell settings put global airplane_mode_on 0")
        time.sleep(2)

        adb(adb_path, "shell svc data enable")

    else:
        log("Invalid mode.")
        return False

    log("Waiting for network...")
    time.sleep(post_wait)

    ip_after = get_public_ip(ip_timeout)

    if not ip_after:
        log("Internet did not come back.")
        return False

    log(f"New IP: {ip_after}")

    return ip_after != ip_before
