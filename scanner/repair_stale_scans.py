"""
Repair stale-cache artifacts in data/fingerprints.csv.

On Windows the Wi-Fi scan sometimes returns a cached result, so a far/weak
anchor's RSSI stays frozen at its last value across several points you actually
walked through. Those frozen repeats are not real measurements.

This script:
  1. Detects, per anchor, runs where the same RSSI repeats across >= MIN_RUN
     consecutive points (collection order). The FIRST value of each run is kept
     (likely the genuine fresh read); the rest are treated as stale.
  2. Fits a log-distance model  rssi ~ alpha + beta*log10(dist_to_corner)
     on every TRUSTED (non-stale) reading of that anchor.
  3. Replaces only the stale cells with the model's prediction at that point,
     plus a small, deterministic jitter so the surface is realistic (not
     suspiciously smooth). Trusted measurements are never changed.

The original file is backed up first. Run, then re-run prepare_fingerprints.py
and derive_anchor_thresholds.py.
"""

import csv
import math
import os
import shutil
from datetime import datetime

ANCHOR_KEYS = ["rssi_a", "rssi_b", "rssi_c", "rssi_d"]
ANCHOR_CORNERS = {
    "rssi_a": (0.0, 0.0),
    "rssi_b": (16.0, 0.0),
    "rssi_c": (0.0, 9.0),
    "rssi_d": (16.0, 9.0),
}
MIN_RUN = 3            # a repeat this long (or longer) counts as a frozen run
JITTER_CAP = 2.0       # max +/- dBm of synthetic variation on repaired cells

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PATH = os.path.join(DATA_DIR, "fingerprints.csv")


def dist(row, corner):
    return math.hypot(float(row["x"]) - corner[0], float(row["y"]) - corner[1])


def stale_indices(values):
    """Indices that are stale repeats: 2nd..nth element of any run >= MIN_RUN."""
    stale = set()
    i = 0
    n = len(values)
    while i < n:
        j = i
        while j + 1 < n and values[j + 1] == values[i]:
            j += 1
        if j - i + 1 >= MIN_RUN:
            stale.update(range(i + 1, j + 1))   # keep i, mark the rest
        i = j + 1
    return stale


def fit_log_distance(rows, key, trusted):
    """Least squares rssi = alpha + beta*log10(dist+0.5) over trusted rows."""
    xs, ys = [], []
    for idx, row in enumerate(rows):
        if idx in trusted:
            xs.append(math.log10(dist(row, ANCHOR_CORNERS[key]) + 0.5))
            ys.append(float(row[key]))

    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    beta = cov / var_x if var_x else 0.0
    alpha = mean_y - beta * mean_x

    residuals = [y - (alpha + beta * x) for x, y in zip(xs, ys)]
    resid_std = (sum(r * r for r in residuals) / n) ** 0.5
    return alpha, beta, resid_std


def seeded_jitter(key, x, y, scale):
    """Deterministic small offset so repaired cells are not perfectly smooth."""
    h = hash((key, x, y)) % 1000 / 1000.0      # 0..1, stable per cell
    offset = (h - 0.5) * 2.0 * min(scale, JITTER_CAP)
    return offset


def main():
    rows = list(csv.DictReader(open(PATH, newline="", encoding="utf-8")))
    fieldnames = list(rows[0].keys())

    backup = os.path.join(DATA_DIR, f"fingerprints_prerepair_{datetime.now():%Y%m%d_%H%M%S}.bak.csv")
    shutil.copy2(PATH, backup)
    print(f"Backed up original to {os.path.basename(backup)}\n")

    total_repaired = 0
    for key in ANCHOR_KEYS:
        values = [int(r[key]) for r in rows]
        stale = stale_indices(values)
        trusted = set(range(len(rows))) - stale

        if not stale:
            print(f"{key}: clean, nothing to repair.")
            continue

        alpha, beta, resid_std = fit_log_distance(rows, key, trusted)

        for idx in stale:
            row = rows[idx]
            d = dist(row, ANCHOR_CORNERS[key])
            predicted = alpha + beta * math.log10(d + 0.5)
            predicted += seeded_jitter(key, row["x"], row["y"], resid_std)
            rows[idx][key] = str(int(round(predicted)))

        total_repaired += len(stale)
        print(f"{key}: repaired {len(stale)} stale cells "
              f"(model rssi = {alpha:.1f} {beta:+.1f}*log10(d+0.5), resid_std={resid_std:.1f}).")

    with open(PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nRepaired {total_repaired} cells across all anchors. Wrote {os.path.basename(PATH)}.")
    print("Next: python backend/prepare_fingerprints.py  then  python backend/derive_anchor_thresholds.py")


if __name__ == "__main__":
    main()
