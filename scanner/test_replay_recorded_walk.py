import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

import replay_recorded_walk


def test_parse_log_lines_extracts_anchor_values_and_recorded_result():
    samples = replay_recorded_walk.parse_log_lines(
        [
            "#1 0.52s A=-59 B=None C=-46 D=-66 -> no prediction",
            "#2 1.58s A=-51 B=-56 C=-37 D=-53 -> x=3.13 y=3.47 conf=0.95 live",
        ]
    )

    assert len(samples) == 2
    assert samples[0].scan_id == 1
    assert samples[0].loop_seconds == 0.52
    assert samples[0].rssi == {
        "rssi_a": -59,
        "rssi_b": None,
        "rssi_c": -46,
        "rssi_d": -66,
    }
    assert samples[0].recorded_location is None
    assert samples[1].recorded_location == {
        "x": 3.13,
        "y": 3.47,
        "confidence": 0.95,
        "status": "live",
    }


def test_build_replay_body_matches_scanner_payload_shape():
    sample = replay_recorded_walk.ReplaySample(
        scan_id=9,
        loop_seconds=0.74,
        rssi={"rssi_a": -60, "rssi_b": -54, "rssi_c": -40, "rssi_d": -50},
        recorded_location={"x": 4.22, "y": 3.98, "confidence": 0.84, "status": "live"},
    )

    body = replay_recorded_walk.build_replay_body(
        sample,
        scan_started_at="2026-06-06T12:00:00.000",
        scan_finished_at="2026-06-06T12:00:00.740",
    )

    assert body["rssi_a"] == -60
    assert body["rssi_b"] == -54
    assert body["rssi_c"] == -40
    assert body["rssi_d"] == -50
    assert body["carried"] == []
    assert body["scan_id"] == 9
    assert body["network_count"] == 0
    assert body["replay"] is True
    assert body["recorded_scan_id"] == 9
    assert body["recorded_loop_seconds"] == 0.74
