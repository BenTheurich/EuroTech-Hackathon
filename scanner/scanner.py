import argparse
import json
import os
import time
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

DEFAULT_SCAN_INTERVAL_SECONDS = 0
DEFAULT_SCAN_WAIT_SECONDS = 0.75
DEFAULT_BACKEND_URL = "http://localhost:8000/api/location-data"
REQUEST_TIMEOUT_SECONDS = 1.0

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LATEST_SCAN_PATH = os.path.join(DATA_DIR, "latest_scan.json")

last_known = {
    key: None for key in ANCHOR_KEYS
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Live Wi-Fi anchor scanner.")
    parser.add_argument(
        "--scan-wait",
        type=float,
        default=_env_float("RMFINDR_SCAN_WAIT", DEFAULT_SCAN_WAIT_SECONDS),
        help="Seconds to wait after triggering a Wi-Fi scan before reading results.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=_env_float("RMFINDR_SCAN_INTERVAL", DEFAULT_SCAN_INTERVAL_SECONDS),
        help="Extra seconds to wait between scan loops.",
    )
    parser.add_argument(
        "--backend-url",
        default=os.getenv("RMFINDR_BACKEND_URL", DEFAULT_BACKEND_URL),
        help="Backend /api/location-data URL.",
    )
    parser.add_argument(
        "--quiet",
        dest="quiet",
        action="store_true",
        default=_env_bool("RMFINDR_QUIET", True),
        help="Print compact one-line scan status.",
    )
    parser.add_argument(
        "--verbose",
        dest="quiet",
        action="store_false",
        help="Print detailed network/anchor scan status.",
    )
    parser.add_argument(
        "--no-write-latest",
        dest="write_latest",
        action="store_false",
        default=True,
        help="Skip writing data/latest_scan.json each loop.",
    )
    parser.add_argument(
        "--no-send",
        dest="send_to_backend",
        action="store_false",
        default=True,
        help="Scan only; do not POST to the backend.",
    )
    return parser.parse_args(argv)


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


def scan_wifi_networks(interface, scan_wait_seconds=DEFAULT_SCAN_WAIT_SECONDS):
    """
    Triggers a real Wi-Fi scan using the Windows WLAN API through pywifi.
    """
    interface.scan()
    time.sleep(scan_wait_seconds)

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
            "approximate_dbm": approximate_dbm,
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
    the set of anchor keys that had to be carried forward.
    """
    carried = set()

    for anchor_key in ANCHOR_KEYS:
        if payload[anchor_key] is not None:
            last_known[anchor_key] = payload[anchor_key]
        elif last_known[anchor_key] is not None:
            payload[anchor_key] = last_known[anchor_key]
            carried.add(anchor_key)

    return payload, carried


def build_backend_body(
    payload,
    carried,
    scan_id,
    scan_started_at,
    scan_finished_at,
    scan_wait_seconds,
    network_count,
):
    body = {
        "timestamp": payload.get("timestamp"),
        **{key: payload[key] for key in ANCHOR_KEYS},
        "carried": sorted(carried),
        "scan_id": scan_id,
        "scan_started_at": scan_started_at,
        "scan_finished_at": scan_finished_at,
        "scan_wait_seconds": scan_wait_seconds,
        "network_count": network_count,
    }
    return body


def save_latest_scan(payload):
    ensure_data_folder_exists()

    with open(LATEST_SCAN_PATH, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def send_to_backend(session, body, backend_url, quiet):
    """
    POSTs the RSSI scan to the backend, which runs the
    KNN model and broadcasts the predicted (x, y) to the frontend map.
    Skips sending if any anchor is still unknown (KNN needs all four).
    """
    if any(body[key] is None for key in ANCHOR_KEYS):
        if quiet:
            print("skip missing anchors")
        else:
            print("Skipping backend send: not all 4 anchors seen yet.")
        return None

    try:
        response = session.post(backend_url, json=body, timeout=REQUEST_TIMEOUT_SECONDS)

        if response.status_code == 200:
            return response.json().get("predicted_location")

        print(f"Backend returned status {response.status_code}: {response.text}")
        return None

    except requests.exceptions.ConnectionError:
        print(f"Could not reach backend at {backend_url}. Is it running?")
    except requests.exceptions.Timeout:
        print("Backend request timed out.")

    return None


def print_compact_status(scan_id, body, carried, location, loop_seconds):
    anchors = " ".join(
        f"{key[-1].upper()}={body[key]}{'*' if key in carried else ''}"
        for key in ANCHOR_KEYS
    )
    position = "no prediction"
    if location:
        position = (
            f"x={location.get('x')} y={location.get('y')} "
            f"conf={location.get('confidence')} {location.get('status')}"
        )

    print(f"#{scan_id} {loop_seconds:.2f}s {anchors} -> {position}")


def print_verbose_status(payload, debug_info, carried, scan_wait_seconds, loop_seconds):
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

    print("\nPayload:")
    print(payload)
    print(f"\nScan wait {scan_wait_seconds}s, loop took {loop_seconds:.2f}s.\n")


def main(argv=None):
    args = parse_args(argv)
    print("Starting auto-refresh Wi-Fi anchor scanner.")
    print("Press CTRL + C to stop.\n")
    print(
        "Config: "
        f"scan_wait={args.scan_wait}s interval={args.interval}s "
        f"quiet={args.quiet} backend={args.backend_url}"
    )

    interface = get_wifi_interface()
    session = requests.Session()
    scan_id = 0

    while True:
        try:
            scan_id += 1
            loop_started = time.perf_counter()
            scan_started_at = datetime.now().isoformat(timespec="milliseconds")
            networks = scan_wifi_networks(interface, args.scan_wait)
            scan_finished_at = datetime.now().isoformat(timespec="milliseconds")
            payload, debug_info = find_anchor_signals(networks)
            payload, carried = apply_carry_forward(payload)

            body = build_backend_body(
                payload,
                carried,
                scan_id,
                scan_started_at,
                scan_finished_at,
                args.scan_wait,
                len(networks),
            )

            if args.write_latest:
                save_latest_scan(body)

            location = None
            if args.send_to_backend:
                location = send_to_backend(session, body, args.backend_url, args.quiet)

            loop_seconds = time.perf_counter() - loop_started
            if args.quiet:
                print_compact_status(scan_id, body, carried, location, loop_seconds)
            else:
                print_verbose_status(payload, debug_info, carried, args.scan_wait, loop_seconds)

            if args.interval > 0:
                time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\nScanner stopped by user.")
            break

        except Exception as error:
            print("Scanner error:")
            print(error)
            print("Retrying in 5 seconds...\n")
            time.sleep(5)


def _env_float(name, default):
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() not in {"0", "false", "no", "off"}


if __name__ == "__main__":
    main()
