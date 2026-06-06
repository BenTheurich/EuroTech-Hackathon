import math


ANCHORS = {
    "rssi_a": {"anchor": "A", "x": 0.0, "y": 0.0, "threshold": -40.0},
    "rssi_b": {"anchor": "B", "x": 7.0, "y": 0.0, "threshold": -47.0},
    "rssi_c": {"anchor": "C", "x": 0.0, "y": 5.0, "threshold": -34.0},
    "rssi_d": {"anchor": "D", "x": 7.0, "y": 5.0, "threshold": -36.0},
}

MIN_HINT_SCORE = 0.5
HIGH_CONFIDENCE_HINT_SCORE = 0.75
HIGH_CONFIDENCE_ANCHOR_WEIGHT = 0.70
NORMAL_ANCHOR_WEIGHT = 0.45
CANDIDATE_CONTEXT_RADIUS_M = 2.5


def detect_anchor_hint(scan, prediction):
    readings = {
        key: _parse_number(scan.get(key))
        for key in ANCHORS
    }
    valid_readings = {
        key: value
        for key, value in readings.items()
        if value is not None
    }
    if not valid_readings:
        return None

    hints = []
    for key, config in ANCHORS.items():
        rssi = readings.get(key)
        if rssi is None:
            continue

        signal_score = _clamp((rssi - config["threshold"] + 4.0) / 8.0, 0.0, 1.0)
        if signal_score < MIN_HINT_SCORE:
            continue

        other_values = [
            value
            for other_key, value in valid_readings.items()
            if other_key != key
        ]
        strongest_other = max(other_values) if other_values else rssi
        margin_score = _clamp((rssi - strongest_other - 2.0) / 8.0, 0.0, 1.0)
        candidate_score = _candidate_context_score(prediction.get("candidates"), config)
        context_score = max(margin_score, candidate_score)
        score = min(signal_score, context_score)

        if score >= MIN_HINT_SCORE:
            hints.append({
                "anchor": config["anchor"],
                "x": config["x"],
                "y": config["y"],
                "score": round(score, 2),
                "_rssi": rssi,
            })

    if not hints:
        return None

    best = max(hints, key=lambda hint: (hint["score"], hint["_rssi"]))
    best.pop("_rssi", None)
    return best


def apply_anchor_hint(prediction, hint):
    adjusted = dict(prediction)
    adjusted["anchor_hint"] = hint

    if hint is None:
        return adjusted

    weight = (
        HIGH_CONFIDENCE_ANCHOR_WEIGHT
        if float(hint["score"]) >= HIGH_CONFIDENCE_HINT_SCORE
        else NORMAL_ANCHOR_WEIGHT
    )
    adjusted["x"] = float(prediction["x"]) * (1 - weight) + float(hint["x"]) * weight
    adjusted["y"] = float(prediction["y"]) * (1 - weight) + float(hint["y"]) * weight
    return adjusted


def _candidate_context_score(candidates, anchor):
    if not candidates:
        return 0.0

    best_score = 0.0
    for candidate in candidates:
        distance = math.hypot(
            float(candidate["x"]) - float(anchor["x"]),
            float(candidate["y"]) - float(anchor["y"]),
        )
        score = _clamp(
            (CANDIDATE_CONTEXT_RADIUS_M - distance) / CANDIDATE_CONTEXT_RADIUS_M,
            0.0,
            1.0,
        )
        best_score = max(best_score, score)

    return best_score


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


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))
