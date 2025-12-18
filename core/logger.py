import subprocess
import os


def start_radio_capture(adb_path, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Clean buffer first
    subprocess.run(f'"{adb_path}" logcat -b radio -c', shell=True)

    proc = subprocess.Popen(
        f'"{adb_path}" logcat -b radio -v time',
        shell=True,
        stdout=open(filepath, "w", encoding="utf-8"),
        stderr=subprocess.DEVNULL
    )

    return proc


def stop_radio_capture(proc):
    if proc:
        proc.terminate()
