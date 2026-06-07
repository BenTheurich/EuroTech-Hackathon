import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean


ANCHOR_COLUMNS = ("rssi_a", "rssi_b", "rssi_c", "rssi_d")
FIELDNAMES = ("timestamp", "x", "y", "z", *ANCHOR_COLUMNS)
GRID_X = range(0, 8)
GRID_Y = range(0, 6)
LAPTOP_Z = "-1.0"
SYNTHETIC_WEIGHT = 0.65
IDW_POWER = 2.0

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "fingerprints_clean.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "fingerprints_blended.csv"

# Calibrated from the quick route C -> D -> B -> A on 2026-06-06.
# Values are corner-level estimates, not ground truth.
CALIBRATED_CORNERS = {
    (0, 0): {
        "rssi_a": -32.3,
        "rssi_b": -58.1,
        "rssi_c": -50.3,
        "rssi_d": -61.3,
    },
    (7, 0): {
        "rssi_a": -56.1,
        "rssi_b": -43.0,
        "rssi_c": -50.7,
        "rssi_d": -63.0,
    },
    (0, 5): {
        "rssi_a": -59.0,
        "rssi_b": -66.0,
        "rssi_c": -27.0,
        "rssi_d": -63.5,
    },
    (7, 5): {
        "rssi_a": -66.4,
        "rssi_b": -61.0,
        "rssi_c": -47.6,
        "rssi_d": -34.0,
    },
}


def synthetic_rssi_at_point(x, y, anchor):
    point = (float(x), float(y))
    exact_corner = CALIBRATED_CORNERS.get((int(point[0]), int(point[1])))
    if exact_corner is not None and point == (int(point[0]), int(point[1])):
        return exact_corner[anchor]

    weighted_total = 0.0
    total_weight = 0.0

    for corner, readings in CALIBRATED_CORNERS.items():
        distance = math.dist(point, corner)
        weight = 1 / max(distance, 0.001) ** IDW_POWER
        weighted_total += readings[anchor] * weight
        total_weight += weight

    return round(weighted_total / total_weight, 1)


def blend_rssi(real_value, synthetic_value, synthetic_weight=SYNTHETIC_WEIGHT):
    real_weight = 1 - synthetic_weight
    return round(real_value * real_weight + synthetic_value * synthetic_weight, 1)


def generate_blended_rows(source_path=DEFAULT_SOURCE, synthetic_weight=SYNTHETIC_WEIGHT):
    point_means = _load_point_means(source_path)
    rows = []

    for y in GRID_Y:
        for x in GRID_X:
            point = (float(x), float(y))
            real_readings = point_means.get(point, {})
            row = {
                "timestamp": "blended-calibrated",
                "x": str(x),
                "y": str(y),
                "z": LAPTOP_Z,
            }

            for anchor in ANCHOR_COLUMNS:
                synthetic = synthetic_rssi_at_point(x, y, anchor)
                real = real_readings.get(anchor, synthetic)
                row[anchor] = _format_number(
                    blend_rssi(real, synthetic, synthetic_weight)
                )

            rows.append(row)

    return rows


def write_blended_fingerprints(
    source_path=DEFAULT_SOURCE,
    output_path=DEFAULT_OUTPUT,
    synthetic_weight=SYNTHETIC_WEIGHT,
):
    output_path = Path(output_path)
    rows = generate_blended_rows(source_path, synthetic_weight)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "rows": len(rows),
        "output_path": str(output_path),
        "synthetic_weight": synthetic_weight,
    }


def _load_point_means(source_path):
    source_path = Path(source_path)
    grouped = defaultdict(lambda: {anchor: [] for anchor in ANCHOR_COLUMNS})

    with source_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            point = (_required_number(row, "x"), _required_number(row, "y"))
            for anchor in ANCHOR_COLUMNS:
                value = _parse_number(row.get(anchor))
                if value is not None:
                    grouped[point][anchor].append(value)

    return {
        point: {
            anchor: mean(values)
            for anchor, values in readings.items()
            if values
        }
        for point, readings in grouped.items()
    }


def _required_number(row, column):
    value = _parse_number(row.get(column))
    if value is None:
        raise ValueError(f"Fingerprint row is missing numeric {column}: {row}")
    return value


def _parse_number(value):
    if value is None:
        return None

    text = str(value).strip()
    if text == "" or text.lower() == "none":
        return None

    try:
        return float(text)
    except ValueError:
        return None


def _format_number(value):
    if float(value).is_integer():
        return str(int(value))

    return f"{value:.1f}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate a route-calibrated blended Wi-Fi fingerprint CSV."
    )
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Clean fingerprint CSV input.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Blended fingerprint CSV output.")
    parser.add_argument(
        "--synthetic-weight",
        type=float,
        default=SYNTHETIC_WEIGHT,
        help="How strongly to weight the route-calibrated synthetic prior.",
    )
    args = parser.parse_args()

    stats = write_blended_fingerprints(
        args.source,
        args.output,
        args.synthetic_weight,
    )

    print(
        f"Wrote {stats['rows']} blended fingerprint rows to "
        f"{stats['output_path']} using synthetic_weight={stats['synthetic_weight']}"
    )


if __name__ == "__main__":
    main()
