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


def phone_wifi_on(adb_path):
    return adb(adb_path, "shell settings get global wifi_on") == "1"


def set_phone_wifi(adb_path, enabled):
    # With the phone's Wi-Fi on, USB tethering exits through the home network
    # instead of mobile data, so the public IP being measured is not the carrier's.
    adb(adb_path, f"shell svc wifi {'enable' if enabled else 'disable'}")


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

    elif mode == "C":
        # `settings put global airplane_mode_on` only writes the setting (a logical flag),
        # which is why modes A/B rarely detach the radio. `cmd connectivity airplane-mode`
        # goes through ConnectivityService and really powers the radio off and on.
        # Works without root on Android 12+ (tested on Android 16, where the old
        # AIRPLANE_MODE broadcast throws SecurityException).
        log("Mode C → cmd connectivity airplane-mode (real radio toggle)")

        adb(adb_path, "shell cmd connectivity airplane-mode enable")
        time.sleep(airplane_wait)
        adb(adb_path, "shell cmd connectivity airplane-mode disable")

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
