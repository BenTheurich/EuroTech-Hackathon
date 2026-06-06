from datetime import datetime, timedelta, timezone

import pytest

from location_tracker import LocationTracker, confidence_from_distance


def test_confidence_is_high_near_fingerprint_and_low_for_far_distance():
    assert confidence_from_distance(4.0, carried_count=0) == pytest.approx(1.0)
    assert confidence_from_distance(20.0, carried_count=0) == pytest.approx(0.15)


def test_carried_anchors_reduce_confidence():
    assert confidence_from_distance(8.0, carried_count=2) == pytest.approx(0.45)


def test_tracker_accepts_normal_walking_movement():
    tracker = LocationTracker(max_speed_mps=2.5, slack_m=0.35)
    first_time = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    second_time = first_time + timedelta(seconds=1)

    first = tracker.update(
        {"x": 1.0, "y": 1.0, "nearest_distance": 4.0},
        {"timestamp": first_time.isoformat()},
        now=first_time,
    )
    second = tracker.update(
        {"x": 2.0, "y": 1.0, "nearest_distance": 4.0},
        {"timestamp": second_time.isoformat()},
        now=second_time,
    )

    assert first["status"] == "live"
    assert second["status"] == "live"
    assert second["x"] == pytest.approx(2.0)
    assert second["confidence"] == pytest.approx(1.0)


def test_tracker_caps_room_crossing_jump_and_marks_constrained():
    tracker = LocationTracker(max_speed_mps=2.5, slack_m=0.35)
    first_time = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    second_time = first_time + timedelta(seconds=1)

    tracker.update(
        {"x": 0.0, "y": 0.0, "nearest_distance": 4.0},
        {"timestamp": first_time.isoformat()},
        now=first_time,
    )
    constrained = tracker.update(
        {"x": 7.0, "y": 0.0, "nearest_distance": 4.0},
        {"timestamp": second_time.isoformat()},
        now=second_time,
    )

    assert constrained["status"] == "constrained"
    assert constrained["x"] == pytest.approx(2.85)
    assert constrained["y"] == pytest.approx(0.0)
    assert constrained["raw_x"] == pytest.approx(7.0)
    assert constrained["raw_y"] == pytest.approx(0.0)
    assert constrained["confidence"] == pytest.approx(0.75)


def test_tracker_prefers_local_candidates_over_far_raw_prediction():
    tracker = LocationTracker(max_speed_mps=1.4, slack_m=0.25)
    first_time = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    second_time = first_time + timedelta(seconds=1)

    tracker.update(
        {"x": 3.0, "y": 4.0, "nearest_distance": 4.0},
        {"timestamp": first_time.isoformat()},
        now=first_time,
    )
    fused = tracker.update(
        {
            "x": 7.0,
            "y": 4.0,
            "nearest_distance": 5.0,
            "candidates": [
                {"x": 7.0, "y": 4.0, "distance": 5.0},
                {"x": 3.0, "y": 4.0, "distance": 5.4},
                {"x": 4.0, "y": 4.0, "distance": 6.0},
            ],
        },
        {"timestamp": second_time.isoformat()},
        now=second_time,
    )

    assert fused["status"] == "live"
    assert fused["raw_x"] == pytest.approx(7.0)
    assert fused["x"] < 4.0


def test_tracker_payload_includes_public_websocket_fields():
    tracker = LocationTracker()
    now = datetime(2026, 6, 6, 12, 0, 1, tzinfo=timezone.utc)

    payload = tracker.update(
        {"x": 1.0, "y": 2.0, "nearest_distance": 5.0},
        {
            "timestamp": "2026-06-06T12:00:00+00:00",
            "carried": ["rssi_b"],
        },
        now=now,
    )

    assert set(payload) == {
        "x",
        "y",
        "raw_x",
        "raw_y",
        "confidence",
        "status",
        "nearest_distance",
        "scan_age_ms",
        "carried",
        "timestamp",
    }
    assert payload["scan_age_ms"] == 1000
    assert payload["carried"] == ["rssi_b"]
    assert payload["timestamp"] == now.isoformat()
