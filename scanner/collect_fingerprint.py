"""
Fingerprint collector for KNN training (Windows, run with `py`).

Walks you through every point of the room grid in a snake (boustrophedon)
pattern. At each point you stand still, press Enter, and it records ONE Wi-Fi
scan as a single row in data/fingerprints.csv. After each point it tells you
which way to move next.

Grid:  x = 0..16 (17 values), y = 0..9 (10 values) -> 170 points.
Snake order (you never backtrack across the room):
    y=0:  x 0 -> 16   (walk right)
    y=1:  x 16 -> 0   (step forward 1, walk left)
    y=2:  x 0 -> 16   (step forward 1, walk right)
    ...

Anchors (Android phone hotspots, 5 GHz) sit at the four corners on the same
plane as the laptop:
    Anchor_A (0,0)   Anchor_B (16,0)   Anchor_C (0,9)   Anchor_D (16,9)

Before you start: set ANCHOR_SSIDS below to your four hotspot names.

Usage:
    py scanner\\collect_fingerprint.py              # guided snake walk (resumes)
    py scanner\\collect_fingerprint.py --redo        # back up old CSV, start fresh
    py scanner\\collect_fingerprint.py --x 3 --y 2   # (re)collect a single point
    py scanner\\collect_fingerprint.py --scan-wait 2.5
"""

import argparse
import csv
import os
import shutil
import time
from datetime import datetime

import pywifi


# ============================================================
# CONFIGURATION  (edit the SSIDs to match your Android hotspot names)
# ============================================================

ANCHOR_SSIDS = {
    "rssi_a": ["Anchor_A"],
    "rssi_b": ["Anchor_B"],
    "rssi_c": ["Anchor_C"],
    "rssi_d": ["Anchor_D"],
}

# Where each anchor physically sits, just for on-screen guidance.
ANCHOR_POSITIONS = {
    "rssi_a": (0, 0),
    "rssi_b": (16, 0),
    "rssi_c": (0, 9),
    "rssi_d": (16, 9),
}

ANCHOR_KEYS = ["rssi_a", "rssi_b", "rssi_c", "rssi_d"]

# Room grid (number of steps -> inclusive ranges).
X_VALUES = list(range(0, 17))   # 0,1,...,16
Y_VALUES = list(range(0, 10))   # 0,1,...,9

SAMPLES_PER_POINT = 1           # one scan per point, as requested
SCAN_WAIT_SECONDS = 2.0         # let the 5 GHz scan finish before reading
LAPTOP_Z = 0                    # laptop on the same plane as the phones

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FINGERPRINTS_PATH = os.path.join(DATA_DIR, "fingerprints.csv")
CLEAN_PATH = os.path.join(DATA_DIR, "fingerprints_clean.csv")

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


def scan_wifi_networks(interface, scan_wait_seconds=SCAN_WAIT_SECONDS):
    interface.scan()
    time.sleep(scan_wait_seconds)

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

        for row in reader:
            try:
                key = (float(row["x"]), float(row["y"]))
            except (KeyError, ValueError):
                continue
            counts[key] = counts.get(key, 0) + 1

    return counts


def backup_existing_csv():
    """Move existing raw + clean CSVs aside so old/new grids never mix."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    moved = []

    for path in (FINGERPRINTS_PATH, CLEAN_PATH):
        if os.path.exists(path):
            name = os.path.splitext(os.path.basename(path))[0]
            backup_path = os.path.join(DATA_DIR, f"{name}_{stamp}.bak.csv")
            shutil.move(path, backup_path)
            moved.append(os.path.basename(backup_path))

    return moved


def append_row(row):
    ensure_data_folder_exists()
    file_exists = os.path.exists(FINGERPRINTS_PATH)

    with open(FINGERPRINTS_PATH, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def make_row(x, y, reading):
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "x": x,
        "y": y,
        "z": LAPTOP_Z,
        "rssi_a": reading["rssi_a"],
        "rssi_b": reading["rssi_b"],
        "rssi_c": reading["rssi_c"],
        "rssi_d": reading["rssi_d"],
    }


# ============================================================
# COLLECTION
# ============================================================

def build_snake_grid():
    """Boustrophedon order: alternate rows reverse direction on the x axis."""
    grid = []
    for row_index, y in enumerate(Y_VALUES):
        xs = X_VALUES if row_index % 2 == 0 else list(reversed(X_VALUES))
        for x in xs:
            grid.append((x, y))
    return grid


def describe_move(current, nxt):
    cx, cy = current
    nx, ny = nxt
    dx, dy = nx - cx, ny - cy

    if dy > 0:
        return (f"--> ROW DONE. Step 1 FORWARD (+Y) to x={nx}, y={ny}, "
                f"then walk back along the X axis.")
    if dx > 0:
        return f"--> Move 1 step RIGHT (+X) to x={nx}, y={ny}."
    if dx < 0:
        return f"--> Move 1 step LEFT (-X) to x={nx}, y={ny}."
    return f"--> Move to x={nx}, y={ny}."


def scan_point_with_retry(interface, x, y, scan_wait):
    """
    One scan at (x, y). If an anchor is missing, offer a re-scan, because with
    a single sample per point a missing anchor leaves that point with no data.

    Returns a row dict, or None if the user chose to skip the point.
    """
    while True:
        print("  Scanning... hold still.")
        reading = find_anchor_signals(scan_wifi_networks(interface, scan_wait))
        missing = [k for k in ANCHOR_KEYS if reading[k] is None]

        print(
            f"    A={reading['rssi_a']} B={reading['rssi_b']} "
            f"C={reading['rssi_c']} D={reading['rssi_d']}  "
            f"[{'OK' if not missing else 'MISSING ' + ', '.join(missing)}]"
        )

        if not missing:
            return make_row(x, y, reading)

        choice = input(
            "  Missing anchor(s). Enter = re-scan,  c = keep anyway,  s = skip point: "
        ).strip().lower()

        if choice == "c":
            return make_row(x, y, reading)
        if choice == "s":
            return None
        # anything else -> re-scan


def print_anchor_reference():
    print("Anchor corners (Android hotspots, 5 GHz, same plane as laptop):")
    for key in ANCHOR_KEYS:
        ax, ay = ANCHOR_POSITIONS[key]
        names = " / ".join(ANCHOR_SSIDS[key])
        print(f"  {key.upper():7} ({ax}, {ay})   SSID: {names}")
    print()


def guided_walk(interface, scan_wait, redo):
    if redo:
        moved = backup_existing_csv()
        if moved:
            print(f"Backed up previous data to: {', '.join(moved)}\n")
        counts = {}
    else:
        counts = load_existing_counts()

    grid = build_snake_grid()
    total = len(grid)

    print(f"Snake collection: {total} points "
          f"({len(X_VALUES)} x-values x {len(Y_VALUES)} y-values), "
          f"1 scan each, scan wait {scan_wait}s.\n")
    print_anchor_reference()

    for index, (x, y) in enumerate(grid):
        if not redo and counts.get((float(x), float(y)), 0) >= SAMPLES_PER_POINT:
            print(f"[{index + 1}/{total}] ({x}, {y}) already collected. Skipping.")
            continue

        print(f"\n[{index + 1}/{total}] Stand at  x = {x},  y = {y}.")
        choice = input("  Press Enter to scan  (s = skip,  q = quit): ").strip().lower()

        if choice == "q":
            print("\nStopping. Progress so far is saved.")
            return
        if choice == "s":
            print("  Skipped.")
            continue

        row = scan_point_with_retry(interface, x, y, scan_wait)
        if row is None:
            print("  Skipped (no usable scan).")
            continue

        append_row(row)
        print(f"  Saved ({x}, {y}).")

        is_last = index == total - 1
        if is_last:
            print("\nDone. Full grid collected.")
        else:
            print("  " + describe_move((x, y), grid[index + 1]))

    print("\nDone. End of grid.")


def single_point(interface, scan_wait, x, y):
    print_anchor_reference()
    print(f"Collecting a single point at x = {x}, y = {y}.")
    input("  Press Enter to scan: ")
    row = scan_point_with_retry(interface, x, y, scan_wait)
    if row is None:
        print("  Skipped (no usable scan).")
        return
    append_row(row)
    print(f"  Saved ({x}, {y}) to data/fingerprints.csv")


def main():
    parser = argparse.ArgumentParser(description="Collect Wi-Fi fingerprints for KNN training.")
    parser.add_argument("--x", type=float, help="Collect only this x (requires --y)")
    parser.add_argument("--y", type=float, help="Collect only this y (requires --x)")
    parser.add_argument("--redo", action="store_true",
                        help="Back up the existing CSV and re-collect the whole grid")
    parser.add_argument("--scan-wait", type=float, default=SCAN_WAIT_SECONDS,
                        help="Seconds to wait after triggering a Wi-Fi scan before reading results.")
    args = parser.parse_args()

    interface = get_wifi_interface()

    if args.x is not None and args.y is not None:
        single_point(interface, args.scan_wait, args.x, args.y)
    elif args.x is not None or args.y is not None:
        parser.error("Use --x and --y together for a single point, or neither for the guided walk.")
    else:
        guided_walk(interface, args.scan_wait, args.redo)


if __name__ == "__main__":
    main()
