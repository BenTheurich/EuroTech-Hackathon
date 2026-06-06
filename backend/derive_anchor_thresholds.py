"""
Auto-derive anchor-hint RSSI thresholds from collected fingerprints.

The anchor hint (anchor_hints.py) boosts confidence when a scan looks like it
was taken right next to a corner anchor. The `threshold` per anchor is the RSSI
level at which that hint starts to fire. This script measures, from the real
data, how strong each anchor reads when you are AT or NEAR its corner, and sets
the threshold a small margin below that.

Scoring recap (see anchor_hints.py):
    signal_score = (rssi - threshold + 4) / 8
    fires at  signal_score >= 0.5   ->  rssi >= threshold
    high conf at signal_score >= 0.75 -> rssi >= threshold + 2

So with MARGIN = 2 dBm, a typical near-corner reading lands at "high confidence".

Run:
    python backend/derive_anchor_thresholds.py
    python backend/derive_anchor_thresholds.py --near-radius 2.5 --margin 2
"""

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import median

from anchor_hints import ANCHORS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "anchor_thresholds.json"

ANCHOR_COLUMNS = ("rssi_a", "rssi_b", "rssi_c", "rssi_d")


def choose_source(explicit):
    if explicit:
        return Path(explicit)
    clean = DATA_DIR / "fingerprints_clean.csv"
    raw = DATA_DIR / "fingerprints.csv"
    return clean if clean.exists() else raw


def parse_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_rows(source):
    rows = []
    with open(source, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            x = parse_float(row.get("x"))
            y = parse_float(row.get("y"))
            if x is None or y is None:
                continue
            rows.append((x, y, row))
    return rows


def derive(rows, near_radius, margin):
    results = {}

    for key in ANCHOR_COLUMNS:
        corner = ANCHORS[key]
        cx, cy = corner["x"], corner["y"]

        near = []
        for x, y, row in rows:
            if math.hypot(x - cx, y - cy) > near_radius:
                continue
            rssi = parse_float(row.get(key))
            if rssi is not None:
                near.append(rssi)

        if not near:
            results[key] = {
                "threshold": corner["threshold"],
                "samples": 0,
                "source": "default (no near readings found)",
            }
            continue

        near_median = median(near)
        threshold = round(near_median - margin)
        results[key] = {
            "threshold": float(threshold),
            "samples": len(near),
            "near_min": min(near),
            "near_median": near_median,
            "near_max": max(near),
            "source": "derived",
        }

    return results


def main():
    parser = argparse.ArgumentParser(description="Derive anchor-hint thresholds from fingerprints.")
    parser.add_argument("--source", help="CSV to read (default: fingerprints_clean.csv, else fingerprints.csv)")
    parser.add_argument("--near-radius", type=float, default=2.5,
                        help="How close (in grid steps) a point counts as 'near' its corner.")
    parser.add_argument("--margin", type=float, default=2.0,
                        help="dBm below the near-corner median to place the threshold.")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing the JSON.")
    args = parser.parse_args()

    source = choose_source(args.source)
    if not source.exists():
        parser.error(f"No fingerprint CSV found at {source}. Collect data first.")

    rows = load_rows(source)
    print(f"Read {len(rows)} rows from {source.name}")
    print(f"near-radius = {args.near_radius} steps, margin = {args.margin} dBm\n")

    results = derive(rows, args.near_radius, args.margin)

    print(f"{'anchor':7} {'corner':10} {'n_near':>6} {'min':>6} {'median':>7} {'max':>6} {'->thr':>6}")
    for key in ANCHOR_COLUMNS:
        r = results[key]
        corner = f"({ANCHORS[key]['x']:.0f},{ANCHORS[key]['y']:.0f})"
        if r["source"] == "derived":
            print(f"{key:7} {corner:10} {r['samples']:>6} "
                  f"{r['near_min']:>6.0f} {r['near_median']:>7.1f} {r['near_max']:>6.0f} "
                  f"{r['threshold']:>6.0f}")
        else:
            print(f"{key:7} {corner:10} {r['samples']:>6} "
                  f"{'-':>6} {'-':>7} {'-':>6} {r['threshold']:>6.0f}  ({r['source']})")

    overrides = {key: results[key]["threshold"] for key in ANCHOR_COLUMNS}

    if args.dry_run:
        print("\nDry run. Would write:")
        print(json.dumps(overrides, indent=2))
        return

    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(overrides, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}. The backend will use these on next start.")


if __name__ == "__main__":
    main()
