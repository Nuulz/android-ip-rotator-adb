```markdown
# Experimental Android IP Rotator (ADB)

## Overview

This repository documents a **real, reproducible technical experiment** aimed at checking whether it is possible to force a **public IPv4 rotation** using an Android phone connected to a PC via **USB tethering**, controlling network state **only from the computer using ADB**, with no root access and no system-signed apps.

This is not a “magic solution” repo.  
It’s a boundary test of **how far Android actually lets you go**.

---

## What this project is about

The goal was simple:

- Cut the mobile connection
- Bring it back
- Check if the public IP changes

All of that:
- Using ADB
- Using Python
- Without touching the phone manually once the test starts
- Without VPNs, proxies, or firmware mods

What matters here is not *trying* to rotate the IP, but **proving what does and does not work**.

---

## Technical approach

The script (`check_ip_data.py`) follows this flow:

1. Get the current public IPv4 from the PC
2. Send ADB commands to the phone to change radio state:
   - Toggle airplane mode
   - Optionally toggle mobile data
3. Wait for the network to reconnect
4. Get the public IPv4 again
5. Compare results

Everything is logged, timed, and repeatable.

---

## Available test modes

### Mode A — Airplane only

Sequence:
```

airplane_mode ON → wait → airplane_mode OFF

```

This checks whether a pure radio cut is enough to trigger a new IP.

---

### Mode B — Airplane + Mobile Data

Sequence:
```

airplane_mode ON → mobile data OFF → wait → airplane_mode OFF → mobile data ON

````

This tries to force a deeper network reset, closer to what a human toggle *looks like*.

---

## What actually happens

After multiple real-world tests, the behavior is consistent:

- Airplane mode triggered via ADB (`settings put global airplane_mode_on`)
  **does NOT follow the same internal path** as the UI toggle.
- ADB flips a state flag, but:
  - It does not fully reset the modem
  - It does not invalidate the data session at framework level
- The radio comes back fast, but the network session stays alive

On carrier networks using **CGNAT**, the public IPv4 is usually **sticky**, so quick reconnects just reuse the same mapping.

---

## Final takeaway

This is not a scripting problem.

It’s an **Android architecture limit** by design:

- Deep radio control is blocked without system permissions
- ADB is intentionally sandboxed
- IP assignment is mostly controlled by the carrier

This repo shows **the exact point where normal tools stop working**.

---

## Requirements

- Windows, Linux, or macOS
- Python 3.9+
- ADB installed and working
- Android phone with:
  - USB debugging enabled
  - USB tethering enabled

---

## Setup

1. Clone the repo
2. Install dependencies:

```bash
pip install requests
````

3. Edit the script and set your ADB path:

```python
ADB_PATH = r"PATH_TO_YOUR_ADB/adb"
```

4. Make sure your device is detected:

```bash
adb devices
```

5. Run the script:

```bash
python check_ip_data.py
```

---

## Important notes

* Some ADB commands may not work on all OEMs or Android versions
* Many carriers do not rotate IPv4 on short reconnects
* This script is **experimental**
* Do not treat this as an anonymity tool

---

## Where to go from here

If someone wants to push further, real options are:

* Hidden Telephony APIs
* Shizuku-based permission elevation
* Framework hooks (LSPosed / Xposed)
* Vendor RIL analysis
* Carrier-level IP policy research

None of that is implemented here.

---

## Credits

This project was built independently, with technical assistance from **ChatGPT (OpenAI)** as a reasoning and analysis helper.

All testing, validation, and final conclusions were done by the repository author.

---

## License

Free to use for educational and research purposes.

```
```
