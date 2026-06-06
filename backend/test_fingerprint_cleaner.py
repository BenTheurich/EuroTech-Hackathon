import csv
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parent))

from fingerprint_cleaner import clean_fingerprints


def write_csv(path, rows):
    fieldnames = ["timestamp", "x", "y", "z", "rssi_a", "rssi_b", "rssi_c", "rssi_d"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_cleaner_preserves_rows_and_fills_missing_from_same_point_median(tmp_path):
    source = tmp_path / "fingerprints.csv"
    output = tmp_path / "fingerprints_clean.csv"
    rows = [
        {"timestamp": "t1", "x": "0", "y": "0", "z": "-1.0", "rssi_a": "-40", "rssi_b": "-60", "rssi_c": "-70", "rssi_d": "-80"},
        {"timestamp": "t2", "x": "0", "y": "0", "z": "-1.0", "rssi_a": "-41", "rssi_b": "", "rssi_c": "-71", "rssi_d": "-81"},
        {"timestamp": "t3", "x": "0", "y": "0", "z": "-1.0", "rssi_a": "-42", "rssi_b": "-62", "rssi_c": "-72", "rssi_d": "-82"},
    ]
    write_csv(source, rows)

    stats = clean_fingerprints(source, output)
    cleaned = read_csv(output)

    assert stats["rows"] == 3
    assert len(cleaned) == 3
    assert cleaned[1]["rssi_b"] == "-61"
    assert cleaned[1]["imputed_rssi_b"] == "true"
    assert cleaned[0]["imputed_rssi_b"] == "false"


def test_cleaner_uses_nearest_three_points_when_same_point_anchor_is_missing(tmp_path):
    source = tmp_path / "fingerprints.csv"
    output = tmp_path / "fingerprints_clean.csv"
    rows = [
        {"timestamp": "target", "x": "1", "y": "0", "z": "-1.0", "rssi_a": "-50", "rssi_b": "-60", "rssi_c": "-70", "rssi_d": ""},
        {"timestamp": "left", "x": "0", "y": "0", "z": "-1.0", "rssi_a": "-50", "rssi_b": "-60", "rssi_c": "-70", "rssi_d": "-50"},
        {"timestamp": "right", "x": "2", "y": "0", "z": "-1.0", "rssi_a": "-50", "rssi_b": "-60", "rssi_c": "-70", "rssi_d": "-70"},
        {"timestamp": "up", "x": "1", "y": "1", "z": "-1.0", "rssi_a": "-50", "rssi_b": "-60", "rssi_c": "-70", "rssi_d": "-60"},
        {"timestamp": "far", "x": "7", "y": "5", "z": "-1.0", "rssi_a": "-50", "rssi_b": "-60", "rssi_c": "-70", "rssi_d": "-90"},
    ]
    write_csv(source, rows)

    clean_fingerprints(source, output)
    cleaned = read_csv(output)

    assert cleaned[0]["rssi_d"] == "-60"
    assert cleaned[0]["imputed_rssi_d"] == "true"
    assert all(row["rssi_d"] for row in cleaned)
