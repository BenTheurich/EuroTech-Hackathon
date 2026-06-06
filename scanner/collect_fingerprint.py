"""
Fingerprint collector for KNN training (Windows, run with `py`).

Walks you through every point of the room grid. At each point you stand still,
press Enter, and it records 5 Wi-Fi scans as 5 separate rows in
data/fingerprints.csv (keeping the natural signal variation, which helps KNN).

Room: 7 m (x = width, left/right) by 5 m (y = length, forward/back).
Grid:  x = 0..7 (8 values), y = 0..5 (6 values) -> 48 points.
Order: y outer, x inner -> all of y=0 first (x=0..7), then y=1, etc.

Anchors (phone hotspots) sit at the four corners on the z=0 plane:
    Anchor_A (0,0)   Anchor_B (7,0)   Anchor_C (0,5)   Anchor_D (7,5)
The laptop measures on the z = -1 plane (recorded as a constant for the record).

Usage:
    py scanner\\collect_fingerprint.py              # guided walk over the whole grid
    py scanner\\collect_fingerprint.py --redo        # re-collect everything from scratch
    py scanner\\collect_fingerprint.py --x 3 --y 2   # (re)collect a single point only
"""

import argparse
import csv
import os
import time
from datetime import datetime

import pywifi


# ============================================================
# CONFIGURATION  (edit the SSIDs to match your phone hotspot names)
# ============================================================

ANCHOR_SSIDS = {
    "rssi_a": ["Anchor_A", "iPhone Azerbaijan"],
    "rssi_b": ["Anchor_B"],
    "rssi_c": ["Anchor_C"],
    "rssi_d": ["Anchor_D"],
}

# Where each anchor physically sits, just for on-screen guidance.
ANCHOR_POSITIONS = {
    "rssi_a": (0, 0),
    "rssi_b": (7, 0),
    "rssi_c": (0, 5),
    "rssi_d": (7, 5),
}

ANCHOR_KEYS = ["rssi_a", "rssi_b", "rssi_c", "rssi_d"]

# Room grid.
X_VALUES = list(range(0, 8))   # 0,1,2,3,4,5,6,7
Y_VALUES = list(range(0, 6))   # 0,1,2,3,4,5

SAMPLES_PER_POINT = 5
SCAN_WAIT_SECONDS = 2          # let the Wi-Fi card finish a scan
LAPTOP_Z = -1.0                # measurement plane (constant; for the record)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FINGERPRINTS_PATH = os.path.join(DATA_DIR, "fingerprints.csv")

CSV_FIELDS = ["timestamp", "x", "y", "z", "rssi_a", "rssi_b", "rssi_c", "rssi_d"]


# ============================================================
# WI-FI SCANNING
# ============================================================

def ensure_data_folder_exists():
    os.makedirs(DATA_DIR, exist_ok=True)


def get_wifi_interface():
    wifi = pywifi.PyWiFi()
    interfaces = wifi.interfaces()

    if not interfaces:
        raise RuntimeError("No Wi-Fi interface found. Check whether Wi-Fi is enabled.")

    return interfaces[0]


def signal_to_dbm(signal):
    if signal is None:
        return None

    signal = int(signal)

    if signal < 0:
        return signal

    return int((signal / 2) - 100)


def ssid_matches(detected_ssid, expected_names):
    detected_clean = detected_ssid.strip().lower()

    for expected in expected_names:
        if detected_clean == expected.strip().lower():
            return True

    return False


def scan_wifi_networks(interface):
    interface.scan()
    time.sleep(SCAN_WAIT_SECONDS)

    results = interface.scan_results()
    networks = []

    for result in results:
        networks.append({
            "ssid": (result.ssid or "").strip(),
            "bssid": (result.bssid or "").strip().lower(),
            "rssi": signal_to_dbm(result.signal),
        })

    return networks


def find_anchor_signals(networks):
    """Returns {rssi_a, rssi_b, rssi_c, rssi_d}, strongest match per anchor."""
    reading = {key: None for key in ANCHOR_KEYS}

    for anchor_key, possible_ssids in ANCHOR_SSIDS.items():
        best = None

        for network in networks:
            if network["rssi"] is None:
                continue
            if ssid_matches(network["ssid"], possible_ssids):
                if best is None or network["rssi"] > best["rssi"]:
                    best = network

        if best:
            reading[anchor_key] = best["rssi"]

    return reading


# ============================================================
# CSV
# ============================================================

def load_existing_counts():
    """How many rows already exist per (x, y), so we can resume/skip."""
    counts = {}

    if not os.path.exists(FINGERPRINTS_PATH):
        return counts

    with open(FINGERPRINTS_PATH, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        # Old files may not have rssi_d; that's fine for counting.
        for row in reader:
            try:
                key = (float(row["x"]), float(row["y"]))
            except (KeyError, ValueError):
                continue
            counts[key] = counts.get(key, 0) + 1

    return counts


def append_rows(rows):
    ensure_data_folder_exists()
    file_exists = os.path.exists(FINGERPRINTS_PATH)

    with open(FINGERPRINTS_PATH, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)

        if not file_exists:
            writer.writeheader()

        for row in rows:
            writer.writerow(row)


# ============================================================
# COLLECTION
# ============================================================

def collect_point(interface, x, y):
    """Runs SAMPLES_PER_POINT scans at (x, y) and returns that many rows."""
    rows = []
    complete = 0

    print(f"  Scanning {SAMPLES_PER_POINT} times. Hold still...")

    for i in range(SAMPLES_PER_POINT):
        networks = scan_wifi_networks(interface)
        reading = find_anchor_signals(networks)

        missing = [k for k in ANCHOR_KEYS if reading[k] is None]
        status = "OK" if not missing else f"MISSING {', '.join(missing)}"
        if not missing:
            complete += 1

        print(
            f"    scan {i + 1}/{SAMPLES_PER_POINT}: "
            f"A={reading['rssi_a']} B={reading['rssi_b']} "
            f"C={reading['rssi_c']} D={reading['rssi_d']}  [{status}]"
        )

        rows.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "x": x,
            "y": y,
            "z": LAPTOP_Z,
            "rssi_a": reading["rssi_a"],
            "rssi_b": reading["rssi_b"],
            "rssi_c": reading["rssi_c"],
            "rssi_d": reading["rssi_d"],
        })

    if complete < SAMPLES_PER_POINT:
        print(
            f"  Warning: only {complete}/{SAMPLES_PER_POINT} scans saw all 4 anchors. "
            f"Rows with a missing anchor are dropped during KNN training."
        )

    return rows


def print_anchor_reference():
    print("Anchor corners (phones, z=0):")
    for key in ANCHOR_KEYS:
        ax, ay = ANCHOR_POSITIONS[key]
        names = " / ".join(ANCHOR_SSIDS[key])
        print(f"  {key.upper():7} ({ax}, {ay})   SSID: {names}")
    print(f"Laptop measures on the z = {LAPTOP_Z} plane.\n")


def guided_walk(interface, redo):
    counts = {} if redo else load_existing_counts()

    grid = [(x, y) for y in Y_VALUES for x in X_VALUES]  # y outer, x inner
    total = len(grid)

    print(f"Guided collection: {total} points "
          f"({len(X_VALUES)} x-values x {len(Y_VALUES)} y-values), "
          f"{SAMPLES_PER_POINT} scans each.\n")
    print_anchor_reference()

    for index, (x, y) in enumerate(grid, start=1):
        already = counts.get((float(x), float(y)), 0)

        if not redo and already >= SAMPLES_PER_POINT:
            print(f"[{index}/{total}] Point ({x}, {y}) already has {already} rows. Skipping.")
            continue

        print(f"\n[{index}/{total}] Stand at  x = {x} m,  y = {y} m.")
        choice = input("  Press Enter to scan  (s = skip this point,  q = quit): ").strip().lower()

        if choice == "q":
            print("\nStopping. Progress so far is saved.")
            return
        if choice == "s":
            print("  Skipped.")
            continue

        rows = collect_point(interface, x, y)
        append_rows(rows)
        print(f"  Saved {len(rows)} rows to data/fingerprints.csv")

    print("\nDone. Full grid collected.")


def single_point(interface, x, y):
    print_anchor_reference()
    print(f"Collecting a single point at x = {x}, y = {y}.")
    input("  Press Enter to scan: ")
    rows = collect_point(interface, x, y)
    append_rows(rows)
    print(f"  Saved {len(rows)} rows to data/fingerprints.csv")


def main():
    parser = argparse.ArgumentParser(description="Collect Wi-Fi fingerprints for KNN training.")
    parser.add_argument("--x", type=float, help="Collect only this x (requires --y)")
    parser.add_argument("--y", type=float, help="Collect only this y (requires --x)")
    parser.add_argument("--redo", action="store_true", help="Re-collect the whole grid, ignoring existing rows")
    args = parser.parse_args()

    interface = get_wifi_interface()

    if args.x is not None and args.y is not None:
        single_point(interface, args.x, args.y)
    elif args.x is not None or args.y is not None:
        parser.error("Use --x and --y together for a single point, or neither for the guided walk.")
    else:
        guided_walk(interface, args.redo)


if __name__ == "__main__":
    main()
