from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).parent))

from knn_model import WifiKNNLocalizer


def write_fingerprints(path, rows):
    path.write_text(
        "\n".join(
            [
                "timestamp,x,y,z,rssi_a,rssi_b,rssi_c,rssi_d",
                *[
                    f"2026-06-05T18:20:{index:02d},{row['x']},{row['y']},-1.0,"
                    f"{row['rssi_a']},{row['rssi_b']},{row['rssi_c']},{row['rssi_d']}"
                    for index, row in enumerate(rows)
                ],
            ]
        ),
        encoding="utf-8",
    )


def test_predict_location_uses_csv_fingerprints(tmp_path):
    fingerprints_path = tmp_path / "fingerprints.csv"
    write_fingerprints(
        fingerprints_path,
        [
            {"x": 0, "y": 0, "rssi_a": -40, "rssi_b": -80, "rssi_c": -80, "rssi_d": -80},
            {"x": 7, "y": 0, "rssi_a": -80, "rssi_b": -40, "rssi_c": -80, "rssi_d": -80},
            {"x": 0, "y": 5, "rssi_a": -80, "rssi_b": -80, "rssi_c": -40, "rssi_d": -80},
        ],
    )

    localizer = WifiKNNLocalizer(fingerprint_path=fingerprints_path, n_neighbors=1)

    prediction = localizer.predict_location(
        {"rssi_a": -41, "rssi_b": -79, "rssi_c": -81, "rssi_d": -72}
    )

    assert prediction == {"x": pytest.approx(0.0), "y": pytest.approx(0.0)}


def test_default_source_prefers_clean_then_raw_then_sample(tmp_path):
    clean_path = tmp_path / "fingerprints_clean.csv"
    raw_path = tmp_path / "fingerprints.csv"
    sample_path = tmp_path / "sample_fingerprints.csv"

    write_fingerprints(
        sample_path,
        [{"x": 0, "y": 0, "rssi_a": -40, "rssi_b": -80, "rssi_c": -80, "rssi_d": -80}],
    )
    write_fingerprints(
        raw_path,
        [{"x": 1, "y": 1, "rssi_a": -41, "rssi_b": -79, "rssi_c": -79, "rssi_d": -79}],
    )
    write_fingerprints(
        clean_path,
        [{"x": 2, "y": 2, "rssi_a": -42, "rssi_b": -78, "rssi_c": -78, "rssi_d": -78}],
    )

    localizer = WifiKNNLocalizer(data_dir=tmp_path, n_neighbors=1)
    assert localizer.training_source == clean_path

    clean_path.unlink()
    localizer = WifiKNNLocalizer(data_dir=tmp_path, n_neighbors=1)
    assert localizer.training_source == raw_path

    raw_path.unlink()
    localizer = WifiKNNLocalizer(data_dir=tmp_path, n_neighbors=1)
    assert localizer.training_source == sample_path


def test_predict_location_requires_all_four_anchor_values(tmp_path):
    fingerprints_path = tmp_path / "fingerprints.csv"
    write_fingerprints(
        fingerprints_path,
        [{"x": 0, "y": 0, "rssi_a": -40, "rssi_b": -80, "rssi_c": -80, "rssi_d": -80}],
    )

    localizer = WifiKNNLocalizer(fingerprint_path=fingerprints_path, n_neighbors=1)

    with pytest.raises(ValueError, match="rssi_d"):
        localizer.predict_location({"rssi_a": -40, "rssi_b": -80, "rssi_c": -80})
