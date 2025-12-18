import csv
import json
import re


EVENT_PATTERNS = {
    "AIRPLANE_MODE": re.compile(r"AIRPLANE_MODE"),
    "RADIO_POWER": re.compile(r"RADIO_POWER"),
    "DATA_TEARDOWN": re.compile(r"Tear down all data networks"),
    "DATA_ATTACH": re.compile(r"DATA_CONNECTED"),
    "DATA_DETACH": re.compile(r"DATA_DISCONNECTED"),
    "CHANNEL_CHANGE": re.compile(r"mChannelNumber=(\d+)"),
    "BANDWIDTH_CHANGE": re.compile(r"mCellBandwidths=\[([0-9, ]+)\]")
}


def parse_events(log_file):
    events = []

    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            for event_name, pattern in EVENT_PATTERNS.items():
                match = pattern.search(line)
                if match:
                    timestamp = line.split(" ")[0:2]
                    timestamp = " ".join(timestamp)

                    event = {
                        "timestamp": timestamp,
                        "event": event_name,
                        "details": match.groups() if match.groups() else None,
                        "raw": line.strip()
                    }

                    events.append(event)

    return events


def export_json(events, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)


def export_csv(events, output_file):
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["timestamp", "event", "details", "raw"]
        )
        writer.writeheader()
        writer.writerows(events)
