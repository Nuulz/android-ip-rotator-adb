def scan_log_for_markers(logfile):
    markers = {
        "channel_change": "mChannelNumber",
        "bandwidth_change": "mCellBandwidths",
        "airplane": "AIRPLANE_MODE",
        "radio_power": "RADIO"
    }

    found = {k: False for k in markers}

    with open(logfile, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            for key, marker in markers.items():
                if marker in line:
                    found[key] = True

    return found
