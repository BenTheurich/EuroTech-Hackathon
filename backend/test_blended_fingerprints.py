import csv
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parent))

from blended_fingerprints import (
    ANCHOR_COLUMNS,
    CALIBRATED_CORNERS,
    blend_rssi,
    generate_blended_rows,
    synthetic_rssi_at_point,
)


def test_synthetic_prior_matches_calibrated_corners():
    for point, readings in CALIBRATED_CORNERS.items():
        for anchor, expected in readings.items():
            assert synthetic_rssi_at_point(point[0], point[1], anchor) == expected


def test_synthetic_prior_has_stronger_anchor_near_its_corner_than_opposite_corner():
    assert synthetic_rssi_at_point(0, 0, "rssi_a") > synthetic_rssi_at_point(7, 5, "rssi_a")
    assert synthetic_rssi_at_point(7, 0, "rssi_b") > synthetic_rssi_at_point(0, 5, "rssi_b")
    assert synthetic_rssi_at_point(0, 5, "rssi_c") > synthetic_rssi_at_point(7, 0, "rssi_c")
    assert synthetic_rssi_at_point(7, 5, "rssi_d") > synthetic_rssi_at_point(0, 0, "rssi_d")


def test_blend_rssi_weights_synthetic_and_real_values():
    assert blend_rssi(real_value=-60, synthetic_value=-40, synthetic_weight=0.65) == -47.0


def test_generate_blended_rows_writes_full_grid_from_clean_fingerprints(tmp_path):
    source = tmp_path / "fingerprints_clean.csv"
    rows = []
    for y in range(6):
        for x in range(8):
            rows.append({
                "timestamp": "source",
                "x": str(x),
                "y": str(y),
                "z": "-1.0",
                "rssi_a": "-60",
                "rssi_b": "-60",
                "rssi_c": "-60",
                "rssi_d": "-60",
            })

    with source.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["timestamp", "x", "y", "z", *ANCHOR_COLUMNS],
        )
        writer.writeheader()
        writer.writerows(rows)

    blended = generate_blended_rows(source)

    assert len(blended) == 48
    assert blended[0]["x"] == "0"
    assert blended[0]["y"] == "0"
    assert set(ANCHOR_COLUMNS).issubset(blended[0])
    assert blended[-1]["x"] == "7"
    assert blended[-1]["y"] == "5"
