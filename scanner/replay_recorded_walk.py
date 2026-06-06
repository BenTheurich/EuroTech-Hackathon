"""
Replay recorded Wi-Fi anchor scans through the normal backend endpoint.

This acts like the live scanner, except the RSSI source is a saved walk instead
of the Wi-Fi adapter. The backend still runs KNN/tracker logic and broadcasts
to the React frontend over the existing WebSocket.

Run:
    python scanner/replay_recorded_walk.py

Useful options:
    python scanner/replay_recorded_walk.py --no-delay
    python scanner/replay_recorded_walk.py --speed 2
    python scanner/replay_recorded_walk.py --backend-url http://localhost:8000/api/location-data
"""

import argparse
import csv
import json
import math
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests


ANCHOR_KEYS = ("rssi_a", "rssi_b", "rssi_c", "rssi_d")
ANCHOR_LABELS = {
    "rssi_a": "A",
    "rssi_b": "B",
    "rssi_c": "C",
    "rssi_d": "D",
}
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SOURCE_PATH = DATA_DIR / "recorded_anchor_signals.csv"
LATEST_SCAN_PATH = DATA_DIR / "latest_scan.json"
DEFAULT_BACKEND_URL = "http://localhost:8000/api/location-data"
REQUEST_TIMEOUT_SECONDS = 1.0

LOG_LINE_RE = re.compile(
    r"^#(?P<scan_id>\d+)\s+"
    r"(?P<loop_seconds>\d+(?:\.\d+)?)s\s+"
    r"A=(?P<rssi_a>-?\d+|None)\s+"
    r"B=(?P<rssi_b>-?\d+|None)\s+"
    r"C=(?P<rssi_c>-?\d+|None)\s+"
    r"D=(?P<rssi_d>-?\d+|None)\s+"
    r"->\s+(?P<result>.*)$"
)
RECORDED_LOCATION_RE = re.compile(
    r"x=(?P<x>-?\d+(?:\.\d+)?)\s+"
    r"y=(?P<y>-?\d+(?:\.\d+)?)\s+"
    r"conf=(?P<confidence>-?\d+(?:\.\d+)?)\s+"
    r"(?P<status>[a-z_]+)"
)


@dataclass(frozen=True)
class ReplaySample:
    scan_id: int
    loop_seconds: float
    rssi: dict
    recorded_location: dict | None = None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Replay recorded Wi-Fi anchor RSSI values into the backend.",
    )
    parser.add_argument(
        "--source",
        default=str(DEFAULT_SOURCE_PATH),
        help="CSV or raw scanner log file to replay.",
    )
    parser.add_argument(
        "--backend-url",
        default=os.getenv("RMFINDR_BACKEND_URL", DEFAULT_BACKEND_URL),
        help="Backend /api/location-data URL.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Playback speed multiplier when using recorded timing.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Fixed seconds to wait between replayed scans. Overrides recorded timing.",
    )
    parser.add_argument(
        "--no-delay",
        dest="delay",
        action="store_false",
        default=True,
        help="Send all recorded scans as fast as the backend accepts them.",
    )
    parser.add_argument(
        "--loop",
        dest="loop_forever",
        action="store_true",
        help="Replay the recording repeatedly until CTRL+C.",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="First recorded scan id to replay.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of scans to replay.",
    )
    parser.add_argument(
        "--no-send",
        dest="send_to_backend",
        action="store_false",
        default=True,
        help="Print replay rows without POSTing to the backend.",
    )
    parser.add_argument(
        "--no-write-latest",
        dest="write_latest",
        action="store_false",
        default=True,
        help="Skip writing data/latest_scan.json each replay step.",
    )
    parser.add_argument(
        "--quiet",
        dest="quiet",
        action="store_true",
        default=True,
        help="Print compact one-line replay status.",
    )
    parser.add_argument(
        "--verbose",
        dest="quiet",
        action="store_false",
        help="Print full replay payload and backend response.",
    )
    return parser.parse_args(argv)


def load_samples(path):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        samples = load_csv_samples(path)
    else:
        samples = parse_log_lines(path.read_text(encoding="utf-8").splitlines())

    if not samples:
        raise ValueError(f"No replay samples found in {path}.")

    return samples


def parse_log_lines(lines):
    samples = []

    for line in lines:
        match = LOG_LINE_RE.match(line.strip())
        if not match:
            continue

        result = match.group("result")
        samples.append(
            ReplaySample(
                scan_id=int(match.group("scan_id")),
                loop_seconds=float(match.group("loop_seconds")),
                rssi={
                    key: _parse_optional_int(match.group(key))
                    for key in ANCHOR_KEYS
                },
                recorded_location=_parse_recorded_location(result),
            )
        )

    return samples


def load_csv_samples(path):
    samples = []

    with Path(path).open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            recorded_location = None
            if row.get("recorded_x") not in (None, ""):
                recorded_location = {
                    "x": float(row["recorded_x"]),
                    "y": float(row["recorded_y"]),
                    "confidence": float(row["recorded_confidence"]),
                    "status": row["recorded_status"],
                }

            samples.append(
                ReplaySample(
                    scan_id=int(row["scan_id"]),
                    loop_seconds=float(row["loop_seconds"]),
                    rssi={
                        key: _parse_optional_int(row.get(key))
                        for key in ANCHOR_KEYS
                    },
                    recorded_location=recorded_location,
                )
            )

    return samples


def build_replay_body(sample, scan_started_at, scan_finished_at):
    body = {
        "timestamp": scan_finished_at,
        **sample.rssi,
        "carried": [],
        "scan_id": sample.scan_id,
        "scan_started_at": scan_started_at,
        "scan_finished_at": scan_finished_at,
        "scan_wait_seconds": 0,
        "network_count": 0,
        "replay": True,
        "recorded_scan_id": sample.scan_id,
        "recorded_loop_seconds": sample.loop_seconds,
    }

    if sample.recorded_location is not None:
        body["recorded_location"] = sample.recorded_location

    return body


def save_latest_scan(body):
    DATA_DIR.mkdir(exist_ok=True)
    with LATEST_SCAN_PATH.open("w", encoding="utf-8") as file:
        json.dump(body, file, indent=2)


def send_to_backend(session, body, backend_url, quiet):
    if any(body[key] is None for key in ANCHOR_KEYS):
        if quiet:
            print("skip missing anchors")
        else:
            print("Skipping backend send: not all 4 anchors are present.")
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


def print_compact_status(sample, body, location):
    anchors = " ".join(
        f"{ANCHOR_LABELS[key]}={body[key]}"
        for key in ANCHOR_KEYS
    )
    position = _format_location(location)
    recorded = _format_recorded_comparison(sample.recorded_location, location)
    print(f"#{sample.scan_id} {sample.loop_seconds:.2f}s {anchors} -> {position}{recorded}")


def print_verbose_status(sample, body, location):
    print("=" * 80)
    print(f"Recorded scan #{sample.scan_id}")
    print(f"Recorded loop seconds: {sample.loop_seconds:.2f}")
    print("\nPayload:")
    print(json.dumps(body, indent=2))
    print("\nBackend predicted:")
    print(json.dumps(location, indent=2))


def playback_delay(sample, args):
    if not args.delay:
        return 0.0
    if args.interval is not None:
        return max(args.interval, 0.0)
    return max(sample.loop_seconds / args.speed, 0.0)


def main(argv=None):
    args = parse_args(argv)
    if args.speed <= 0:
        raise ValueError("--speed must be greater than 0.")

    samples = [
        sample
        for sample in load_samples(args.source)
        if sample.scan_id >= args.start
    ]
    if args.limit is not None:
        samples = samples[:args.limit]
    if not samples:
        raise ValueError("No samples selected for replay.")

    print("Starting recorded Wi-Fi anchor replay.")
    print("Press CTRL+C to stop.\n")
    print(
        "Config: "
        f"source={args.source} backend={args.backend_url} "
        f"speed={args.speed} interval={args.interval} "
        f"send={args.send_to_backend}"
    )

    session = requests.Session()

    try:
        while True:
            for sample in samples:
                scan_started_at = datetime.now().isoformat(timespec="milliseconds")
                scan_finished_at = datetime.now().isoformat(timespec="milliseconds")
                body = build_replay_body(sample, scan_started_at, scan_finished_at)

                if args.write_latest:
                    save_latest_scan(body)

                location = None
                if args.send_to_backend:
                    location = send_to_backend(session, body, args.backend_url, args.quiet)

                if args.quiet:
                    print_compact_status(sample, body, location)
                else:
                    print_verbose_status(sample, body, location)

                delay = playback_delay(sample, args)
                if delay > 0:
                    time.sleep(delay)

            if not args.loop_forever:
                break
    except KeyboardInterrupt:
        print("\nReplay stopped by user.")


def _parse_optional_int(value):
    if value is None:
        return None

    text = str(value).strip()
    if text == "" or text.lower() == "none":
        return None

    return int(text)


def _parse_recorded_location(result):
    match = RECORDED_LOCATION_RE.search(result)
    if not match:
        return None

    return {
        "x": float(match.group("x")),
        "y": float(match.group("y")),
        "confidence": float(match.group("confidence")),
        "status": match.group("status"),
    }


def _format_location(location):
    if not location:
        return "no prediction"

    ambiguity = location.get("ambiguity") or {}
    anchor_hint = location.get("anchor_hint") or {}
    ambiguous = "!" if ambiguity.get("ambiguous") else ""
    anchor = "none"
    if anchor_hint:
        anchor = f"{anchor_hint.get('anchor')}:{anchor_hint.get('score')}"

    return " ".join(
        [
            f"x={location.get('x')} y={location.get('y')}",
            f"conf={location.get('confidence')} {location.get('status')}",
            f"knn=({_compact_number(location.get('knn_x'))},{_compact_number(location.get('knn_y'))})",
            f"raw=({_compact_number(location.get('raw_x'))},{_compact_number(location.get('raw_y'))})",
            f"nearest={location.get('nearest_distance')}",
            f"amb={ambiguity.get('spread_m')}{ambiguous}",
            f"anchor={anchor}",
            f"held={location.get('held')}",
        ]
    )


def _format_recorded_comparison(recorded_location, location):
    if recorded_location is None:
        return ""

    text = (
        " | recorded "
        f"x={recorded_location['x']} y={recorded_location['y']} "
        f"conf={recorded_location['confidence']} {recorded_location['status']}"
    )

    if location and isinstance(location.get("x"), (int, float)) and isinstance(location.get("y"), (int, float)):
        delta = math.hypot(
            float(location["x"]) - recorded_location["x"],
            float(location["y"]) - recorded_location["y"],
        )
        text += f" delta={delta:.2f}m"

    return text


def _compact_number(value):
    if value is None:
        return "None"

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)


if __name__ == "__main__":
    main()
