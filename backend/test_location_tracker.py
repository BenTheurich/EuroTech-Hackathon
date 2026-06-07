from datetime import datetime, timedelta, timezone

import pytest

from location_tracker import LocationTracker, confidence_from_distance


def test_confidence_is_high_near_fingerprint_and_low_for_far_distance():
    assert confidence_from_distance(4.0, carried_count=0) == pytest.approx(1.0)
    assert confidence_from_distance(20.0, carried_count=0) == pytest.approx(0.15)


def test_carried_anchors_reduce_confidence():
    assert confidence_from_distance(8.0, carried_count=2) == pytest.approx(0.45)


def test_ambiguous_candidate_spread_reduces_confidence():
    tracker = LocationTracker()
    now = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)

    payload = tracker.update(
        {
            "x": 1.0,
            "y": 1.0,
            "nearest_distance": 4.0,
            "ambiguity": {"spread_m": 4.0, "ambiguous": True},
        },
        {"timestamp": now.isoformat()},
        now=now,
    )

    assert payload["confidence"] == pytest.approx(0.65)
    assert payload["status"] == "live"


def test_tracker_accepts_normal_walking_movement():
    tracker = LocationTracker(max_speed_mps=2.5, slack_m=0.35)
    first_time = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    second_time = first_time + timedelta(seconds=1)
    third_time = first_time + timedelta(seconds=2)

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
    third = tracker.update(
        {"x": 2.1, "y": 1.0, "nearest_distance": 4.0},
        {"timestamp": third_time.isoformat()},
        now=third_time,
    )

    assert first["status"] == "live"
    assert second["status"] == "held"
    assert third["held"] is False
    assert third["status"] == "smoothed"
    assert third["x"] > second["x"]
    assert third["confidence"] == pytest.approx(1.0)


def test_tracker_caps_room_crossing_jump_and_marks_constrained():
    tracker = LocationTracker(max_speed_mps=2.5, slack_m=0.35)
    first_time = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    second_time = first_time + timedelta(seconds=1)
    third_time = first_time + timedelta(seconds=2)

    tracker.update(
        {"x": 0.0, "y": 0.0, "nearest_distance": 4.0},
        {"timestamp": first_time.isoformat()},
        now=first_time,
    )
    held = tracker.update(
        {"x": 7.0, "y": 0.0, "nearest_distance": 4.0},
        {"timestamp": second_time.isoformat()},
        now=second_time,
    )
    constrained = tracker.update(
        {"x": 7.0, "y": 0.0, "nearest_distance": 4.0},
        {"timestamp": third_time.isoformat()},
        now=third_time,
    )

    assert held["status"] == "held"
    assert constrained["status"] == "constrained"
    assert constrained["x"] == pytest.approx(0.71)
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

    assert fused["status"] == "held"
    assert fused["raw_x"] == pytest.approx(7.0)
    assert fused["x"] == pytest.approx(3.0)


def test_tracker_holds_one_off_non_anchor_jump():
    tracker = LocationTracker(max_speed_mps=10.0, slack_m=0.0)
    first_time = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    second_time = first_time + timedelta(seconds=1)

    tracker.update(
        {"x": 0.0, "y": 0.0, "nearest_distance": 4.0},
        {"timestamp": first_time.isoformat()},
        now=first_time,
    )
    held = tracker.update(
        {
            "x": 4.0,
            "y": 0.0,
            "nearest_distance": 4.0,
            "ambiguity": {"spread_m": 4.0, "ambiguous": True},
        },
        {"timestamp": second_time.isoformat()},
        now=second_time,
    )

    assert held["status"] == "held"
    assert held["held"] is True
    assert held["x"] == pytest.approx(0.0)
    assert held["raw_x"] == pytest.approx(4.0)


def test_tracker_releases_sustained_non_anchor_movement():
    tracker = LocationTracker(max_speed_mps=10.0, slack_m=0.0)
    first_time = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)

    tracker.update(
        {"x": 0.0, "y": 0.0, "nearest_distance": 4.0},
        {"timestamp": first_time.isoformat()},
        now=first_time,
    )
    tracker.update(
        {"x": 4.0, "y": 0.0, "nearest_distance": 4.0},
        {"timestamp": (first_time + timedelta(seconds=1)).isoformat()},
        now=first_time + timedelta(seconds=1),
    )
    released = tracker.update(
        {"x": 4.1, "y": 0.0, "nearest_distance": 4.0},
        {"timestamp": (first_time + timedelta(seconds=2)).isoformat()},
        now=first_time + timedelta(seconds=2),
    )

    assert released["held"] is False
    assert released["status"] == "smoothed"
    assert released["x"] > 0.9


def test_tracker_near_anchor_hint_bypasses_hold_and_catches_up_faster():
    tracker = LocationTracker()
    first_time = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    second_time = first_time + timedelta(seconds=1)

    tracker.update(
        {"x": 3.0, "y": 3.0, "nearest_distance": 4.0},
        {"timestamp": first_time.isoformat()},
        now=first_time,
    )
    anchored = tracker.update(
        {
            "x": 0.0,
            "y": 0.0,
            "nearest_distance": 4.0,
            "anchor_hint": {"anchor": "A", "x": 0.0, "y": 0.0, "score": 0.8},
        },
        {"timestamp": second_time.isoformat()},
        now=second_time,
    )

    assert anchored["held"] is False
    assert anchored["status"] == "live"
    assert anchored["x"] < 1.0
    assert anchored["y"] < 1.0


def test_tracker_damps_stationary_false_movement_sequence():
    tracker = LocationTracker()
    start = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)
    raw_sequence = [
        {"x": 3.11, "y": 0.91, "nearest_distance": 3.5},
        {"x": 4.0, "y": 1.97, "nearest_distance": 3.5},
        {"x": 4.35, "y": 2.04, "nearest_distance": 3.8},
        {"x": 3.69, "y": 2.35, "nearest_distance": 3.8},
        {"x": 6.0, "y": 2.83, "nearest_distance": 4.0},
        {"x": 5.29, "y": 1.29, "nearest_distance": 4.0},
        {"x": 6.35, "y": 4.0, "nearest_distance": 4.0},
        {"x": 5.0, "y": 4.0, "nearest_distance": 4.0},
        {"x": 4.35, "y": 1.35, "nearest_distance": 4.0},
        {"x": 3.15, "y": 3.52, "nearest_distance": 4.0},
    ]

    outputs = [
        tracker.update(
            prediction,
            {"timestamp": (start + timedelta(seconds=index * 0.8)).isoformat()},
            now=start + timedelta(seconds=index * 0.8),
        )
        for index, prediction in enumerate(raw_sequence)
    ]

    displayed_steps = [
        ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5
        for a, b in zip(outputs[1:], outputs[:-1])
    ]

    assert max(displayed_steps) <= 1.0


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
        "knn_x",
        "knn_y",
        "confidence",
        "status",
        "nearest_distance",
        "filtered_rssi",
        "anchor_hint",
        "ambiguity",
        "held",
        "scan_age_ms",
        "carried",
        "timestamp",
    }
    assert payload["scan_age_ms"] == 1000
    assert payload["carried"] == ["rssi_b"]
    assert payload["timestamp"] == now.isoformat()
    assert payload["held"] is False
