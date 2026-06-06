import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

import profile_scan_rate
import scanner


def test_scanner_cli_defaults_are_fast_demo_friendly():
    args = scanner.parse_args([])

    assert args.scan_wait == 0.75
    assert args.interval == 0
    assert args.quiet is True
    assert args.write_latest is True
    assert args.backend_url == "http://localhost:8000/api/location-data"


def test_scanner_cli_accepts_live_tuning_flags():
    args = scanner.parse_args(
        [
            "--scan-wait",
            "1.25",
            "--interval",
            "0.5",
            "--backend-url",
            "http://192.168.1.50:8000/api/location-data",
            "--no-write-latest",
            "--verbose",
        ]
    )

    assert args.scan_wait == 1.25
    assert args.interval == 0.5
    assert args.backend_url == "http://192.168.1.50:8000/api/location-data"
    assert args.write_latest is False
    assert args.quiet is False


def test_backend_body_preserves_rssi_values_and_adds_metadata():
    body = scanner.build_backend_body(
        {
            "timestamp": "2026-06-06T12:00:00",
            "rssi_a": -50,
            "rssi_b": -60,
            "rssi_c": -70,
            "rssi_d": -80,
        },
        carried={"rssi_b"},
        scan_id=3,
        scan_started_at="2026-06-06T12:00:00",
        scan_finished_at="2026-06-06T12:00:01",
        scan_wait_seconds=0.75,
        network_count=12,
    )

    assert body == {
        "timestamp": "2026-06-06T12:00:00",
        "rssi_a": -50,
        "rssi_b": -60,
        "rssi_c": -70,
        "rssi_d": -80,
        "carried": ["rssi_b"],
        "scan_id": 3,
        "scan_started_at": "2026-06-06T12:00:00",
        "scan_finished_at": "2026-06-06T12:00:01",
        "scan_wait_seconds": 0.75,
        "network_count": 12,
    }


def test_profile_recommendation_uses_first_stable_fast_wait():
    results = [
        {"wait": 0.25, "anchor_hit_rate": 0.5, "p90_loop_seconds": 0.4},
        {"wait": 0.5, "anchor_hit_rate": 0.8, "p90_loop_seconds": 0.6},
        {"wait": 0.75, "anchor_hit_rate": 0.9, "p90_loop_seconds": 0.95},
        {"wait": 1.0, "anchor_hit_rate": 1.0, "p90_loop_seconds": 1.1},
    ]

    assert profile_scan_rate.choose_recommended_wait(results) == 0.75


def test_profile_recommendation_accepts_subsecond_real_loop_results():
    results = [
        {"wait": 0.3, "anchor_hit_rate": 1.0, "p90_loop_seconds": 0.86, "carried_count": 0},
        {"wait": 0.35, "anchor_hit_rate": 1.0, "p90_loop_seconds": 0.89, "carried_count": 0},
        {"wait": 0.4, "anchor_hit_rate": 1.0, "p90_loop_seconds": 0.98, "carried_count": 0},
        {"wait": 0.5, "anchor_hit_rate": 1.0, "p90_loop_seconds": 1.02, "carried_count": 0},
    ]

    assert profile_scan_rate.choose_recommended_wait(results) == 0.3
