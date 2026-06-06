import time
import json
import os
from datetime import datetime

import pywifi
import requests


# ============================================================
# CONFIGURATION
# ============================================================

ANCHOR_SSIDS = {
    "rssi_a": ["Anchor_A", "iPhone Azerbaijan"],
    "rssi_b": ["Anchor_B"],
    "rssi_c": ["Anchor_C"],
    "rssi_d": ["Anchor_D"],
}

ANCHOR_KEYS = ["rssi_a", "rssi_b", "rssi_c", "rssi_d"]

SCAN_INTERVAL_SECONDS = 1
SCAN_WAIT_SECONDS = 1

# Where the backend is listening. Change this if the backend runs on
# another laptop (use that laptop's LAN IP, e.g. http://192.168.1.50:8000/...).
BACKEND_URL = "http://localhost:8000/api/location-data"

# Set to False to scan only (no networking) while debugging Wi-Fi.
SEND_TO_BACKEND = True

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LATEST_SCAN_PATH = os.path.join(DATA_DIR, "latest_scan.json")

# Remembers the last good reading for each anchor. If a hotspot drops out
# of a single scan, we reuse its previous value instead of sending None
# (which would crash the KNN) or freezing the dot.
last_known = {
    key: None for key in ANCHOR_KEYS
}


def ensure_data_folder_exists():
    os.makedirs(DATA_DIR, exist_ok=True)


def get_wifi_interface():
    wifi = pywifi.PyWiFi()
    interfaces = wifi.interfaces()

    if not interfaces:
        raise RuntimeError("No Wi-Fi interface found. Check whether Wi-Fi is enabled.")

    return interfaces[0]


def signal_to_dbm(signal):
    """
    pywifi usually returns signal as a percentage-like value on Windows.
    We convert it to approximate dBm for consistency with our previous script.

    If your laptop returns already-negative dBm values, we keep them.
    """
    if signal is None:
        return None

    signal = int(signal)

    if signal < 0:
        return signal

    return int((signal / 2) - 100)


def scan_wifi_networks(interface):
    """
    Triggers a real Wi-Fi scan using the Windows WLAN API through pywifi.
    """
    interface.scan()
    time.sleep(SCAN_WAIT_SECONDS)

    results = interface.scan_results()

    networks = []

    for result in results:
        ssid = (result.ssid or "").strip()
        bssid = (result.bssid or "").strip().lower()
        signal_raw = int(result.signal)
        approximate_dbm = signal_to_dbm(signal_raw)

        networks.append({
            "ssid": ssid,
            "bssid": bssid,
            "signal_raw": signal_raw,
            "approximate_dbm": approximate_dbm
        })

    return networks


def ssid_matches(detected_ssid, expected_names):
    detected_clean = detected_ssid.strip().lower()

    for expected in expected_names:
        expected_clean = expected.strip().lower()

        if detected_clean == expected_clean:
            return True

    return False


def find_anchor_signals(networks):
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        **{key: None for key in ANCHOR_KEYS},
    }

    debug_info = {}

    for anchor_key, possible_ssids in ANCHOR_SSIDS.items():
        best_match = None

        for network in networks:
            if ssid_matches(network["ssid"], possible_ssids):
                if best_match is None or network["approximate_dbm"] > best_match["approximate_dbm"]:
                    best_match = network

        if best_match:
            payload[anchor_key] = best_match["approximate_dbm"]
            debug_info[anchor_key] = best_match
        else:
            debug_info[anchor_key] = None

    return payload, debug_info


def apply_carry_forward(payload):
    """
    Fills any anchor missing from this scan with its last known value, and
    updates the memory with fresh readings. Returns the filled payload plus
    the set of anchor keys that had to be carried forward (for display).
    """
    carried = set()

    for anchor_key in ANCHOR_KEYS:
        if payload[anchor_key] is not None:
            last_known[anchor_key] = payload[anchor_key]
        elif last_known[anchor_key] is not None:
            payload[anchor_key] = last_known[anchor_key]
            carried.add(anchor_key)

    return payload, carried


def save_latest_scan(payload):
    ensure_data_folder_exists()

    with open(LATEST_SCAN_PATH, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def send_to_backend(payload):
    """
    POSTs the RSSI scan to the backend, which runs the
    KNN model and broadcasts the predicted (x, y) to the frontend map.
    Skips sending if any anchor is still unknown (KNN needs all four).
    """
    if not SEND_TO_BACKEND:
        return

    if any(payload[key] is None for key in ANCHOR_KEYS):
        print("Skipping backend send: not all 4 anchors seen yet.")
        return

    body = {
        key: payload[key]
        for key in ANCHOR_KEYS
    }

    try:
        response = requests.post(BACKEND_URL, json=body, timeout=2)

        if response.status_code == 200:
            location = response.json().get("predicted_location")
            print(f"Backend predicted location: {location}")
        else:
            print(f"Backend returned status {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"Could not reach backend at {BACKEND_URL}. Is it running?")
    except requests.exceptions.Timeout:
        print("Backend request timed out.")


def print_status(payload, debug_info, carried):
    print("=" * 80)
    print("Anchor scan result:\n")

    for anchor_key in ANCHOR_KEYS:
        info = debug_info.get(anchor_key)

        if info:
            print(
                f"{anchor_key}: FOUND | "
                f"SSID: '{info['ssid']}' | "
                f"BSSID: {info['bssid']} | "
                f"Raw signal: {info['signal_raw']} | "
                f"Approx dBm: {info['approximate_dbm']}"
            )
        elif anchor_key in carried:
            print(f"{anchor_key}: CARRIED FORWARD | reused last value: {payload[anchor_key]}")
        else:
            print(f"{anchor_key}: NOT FOUND | expected SSIDs: {ANCHOR_SSIDS[anchor_key]}")

    print("\nPayload written to data/latest_scan.json:")
    print(payload)
    print(f"\nWaiting {SCAN_INTERVAL_SECONDS} seconds...\n")


def main():
    print("Starting auto-refresh Wi-Fi anchor scanner.")
    print("Press CTRL + C to stop.\n")

    interface = get_wifi_interface()

    while True:
        try:
            networks = scan_wifi_networks(interface)
            payload, debug_info = find_anchor_signals(networks)
            payload, carried = apply_carry_forward(payload)

            save_latest_scan(payload)
            send_to_backend(payload)
            print_status(payload, debug_info, carried)

            time.sleep(SCAN_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\nScanner stopped by user.")
            break

        except Exception as error:
            print("Scanner error:")
            print(error)
            print("Retrying in 5 seconds...\n")
            time.sleep(5)


if __name__ == "__main__":
    main()
