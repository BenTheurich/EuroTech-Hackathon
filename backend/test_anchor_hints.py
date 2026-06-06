import pytest

from anchor_hints import apply_anchor_hint, detect_anchor_hint


def test_detects_strong_near_anchor_signal_with_candidate_context():
    prediction = {
        "x": 15.0,
        "y": 8.0,
        "candidates": [{"x": 15.0, "y": 8.0, "distance": 8.44}],
    }
    scan = {"rssi_a": -50, "rssi_b": -49, "rssi_c": -52, "rssi_d": -30}

    hint = detect_anchor_hint(scan, prediction)

    assert hint["anchor"] == "D"
    assert hint["x"] == pytest.approx(16.0)
    assert hint["y"] == pytest.approx(9.0)
    assert hint["score"] >= 0.75


def test_anchor_hint_blends_raw_prediction_toward_anchor():
    prediction = {"x": 6.0, "y": 3.0}
    hint = {"anchor": "D", "x": 7.0, "y": 5.0, "score": 0.8}

    blended = apply_anchor_hint(prediction, hint)

    assert blended["x"] == pytest.approx(6.7)
    assert blended["y"] == pytest.approx(4.4)
    assert blended["anchor_hint"] == hint


def test_weak_or_contextless_anchor_signal_is_ignored():
    prediction = {
        "x": 3.0,
        "y": 2.0,
        "candidates": [{"x": 3.0, "y": 2.0, "distance": 4.0}],
    }
    scan = {"rssi_a": -41, "rssi_b": -43, "rssi_c": -42, "rssi_d": -44}

    assert detect_anchor_hint(scan, prediction) is None
