from datetime import datetime, timezone
import math


MIN_CONFIDENCE = 0.15
LOW_CONFIDENCE_THRESHOLD = 0.5
LOCAL_CANDIDATE_RADIUS_M = 2.25
LOCAL_PRIOR_MIN_NEAREST_DISTANCE = 4.5
JUMP_DAMPING_DISTANCE_M = 1.0
JUMP_DAMPING_ALPHA = 0.25
STATIONARY_DEADBAND_M = 0.65
SUSTAINED_MOVEMENT_UPDATES = 2
ANCHOR_HINT_SPEED_MPS = 4.0
ANCHOR_HINT_SLACK_M = 0.5


def confidence_from_distance(nearest_distance, carried_count=0):
    confidence = 1 - ((float(nearest_distance) - 4) / 16)
    confidence = _clamp(confidence, MIN_CONFIDENCE, 1.0)
    confidence -= 0.15 * int(carried_count)
    return _clamp(confidence, MIN_CONFIDENCE, 1.0)


class LocationTracker:
    def __init__(self, max_speed_mps=1.4, slack_m=0.25):
        self.max_speed_mps = max_speed_mps
        self.slack_m = slack_m
        self.previous_position = None
        self.previous_time = None
        self.pending_position = None
        self.pending_count = 0

    def update(self, raw_prediction, scan_data, now=None):
        now = now or datetime.now(timezone.utc)
        scan_time = _parse_timestamp(scan_data.get("timestamp"))
        carried = _carried_list(scan_data.get("carried"))

        raw_x = float(raw_prediction["x"])
        raw_y = float(raw_prediction["y"])
        nearest_distance = float(raw_prediction["nearest_distance"])
        confidence = confidence_from_distance(nearest_distance, len(carried))
        status = "live" if confidence >= LOW_CONFIDENCE_THRESHOLD else "low_confidence"
        x = raw_x
        y = raw_y
        held = False
        anchor_hint = raw_prediction.get("anchor_hint")

        if self.previous_position is not None and self.previous_time is not None:
            elapsed = max((now - self.previous_time).total_seconds(), 0.0)
            if anchor_hint:
                allowed_distance = ANCHOR_HINT_SPEED_MPS * elapsed + ANCHOR_HINT_SLACK_M
                self.pending_position = None
                self.pending_count = 0
            else:
                allowed_distance = self.max_speed_mps * elapsed + self.slack_m

            if nearest_distance >= LOCAL_PRIOR_MIN_NEAREST_DISTANCE and not anchor_hint:
                local_prediction = _local_candidate_prediction(
                    raw_prediction.get("candidates"),
                    self.previous_position,
                    allowed_distance,
                )
                if local_prediction is not None:
                    x, y = local_prediction

            previous_x, previous_y = self.previous_position
            x, y, held = self._apply_hysteresis(
                previous_x,
                previous_y,
                x,
                y,
                anchor_hint,
            )
            if held:
                status = "held"

            dx = x - previous_x
            dy = y - previous_y
            distance = math.hypot(dx, dy)

            if distance > allowed_distance and distance > 0:
                ratio = allowed_distance / distance
                x = previous_x + dx * ratio
                y = previous_y + dy * ratio
                confidence = _clamp(confidence - 0.25, MIN_CONFIDENCE, 1.0)
                status = "constrained"

            if not anchor_hint:
                damped_x, damped_y = _damp_large_jump(previous_x, previous_y, x, y)
                if (damped_x, damped_y) != (x, y):
                    x = damped_x
                    y = damped_y
                    if status == "live":
                        status = "smoothed"

        self.previous_position = (x, y)
        self.previous_time = now

        return {
            "x": round(x, 2),
            "y": round(y, 2),
            "raw_x": round(raw_x, 2),
            "raw_y": round(raw_y, 2),
            "knn_x": round(float(raw_prediction.get("knn_x", raw_x)), 2),
            "knn_y": round(float(raw_prediction.get("knn_y", raw_y)), 2),
            "confidence": round(confidence, 2),
            "status": status,
            "nearest_distance": round(nearest_distance, 2),
            "filtered_rssi": raw_prediction.get("filtered_rssi"),
            "anchor_hint": anchor_hint,
            "ambiguity": raw_prediction.get("ambiguity", {"spread_m": 0.0, "ambiguous": False}),
            "held": held,
            "scan_age_ms": _scan_age_ms(scan_time, now),
            "carried": carried,
            "timestamp": now.isoformat(),
        }

    def _apply_hysteresis(self, previous_x, previous_y, x, y, anchor_hint):
        if anchor_hint:
            return x, y, False

        candidate = (x, y)
        movement = math.hypot(x - previous_x, y - previous_y)

        if movement <= STATIONARY_DEADBAND_M:
            self.pending_position = None
            self.pending_count = 0
            return previous_x, previous_y, True

        if (
            self.pending_position is not None
            and _distance(candidate, self.pending_position) <= STATIONARY_DEADBAND_M
        ):
            self.pending_count += 1
        else:
            self.pending_position = candidate
            self.pending_count = 1

        if self.pending_count < SUSTAINED_MOVEMENT_UPDATES:
            return previous_x, previous_y, True

        self.pending_position = None
        self.pending_count = 0
        return x, y, False


def _carried_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return sorted(str(item) for item in value)


def _distance(point, other):
    return math.hypot(point[0] - other[0], point[1] - other[1])


def _parse_timestamp(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _scan_age_ms(scan_time, now):
    if scan_time is None:
        return None

    if scan_time.tzinfo is None and now.tzinfo is not None:
        now_for_delta = now.replace(tzinfo=None)
    elif scan_time.tzinfo is not None and now.tzinfo is None:
        now_for_delta = now.replace(tzinfo=scan_time.tzinfo)
    else:
        now_for_delta = now

    return max(int((now_for_delta - scan_time).total_seconds() * 1000), 0)


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _damp_large_jump(previous_x, previous_y, x, y):
    distance = math.hypot(x - previous_x, y - previous_y)
    if distance <= JUMP_DAMPING_DISTANCE_M:
        return x, y

    return (
        previous_x + (x - previous_x) * JUMP_DAMPING_ALPHA,
        previous_y + (y - previous_y) * JUMP_DAMPING_ALPHA,
    )


def _local_candidate_prediction(candidates, previous_position, allowed_distance):
    if not candidates:
        return None

    radius = max(LOCAL_CANDIDATE_RADIUS_M, allowed_distance)
    previous_x, previous_y = previous_position
    local_candidates = []

    for candidate in candidates:
        candidate_x = float(candidate["x"])
        candidate_y = float(candidate["y"])
        movement_distance = math.hypot(candidate_x - previous_x, candidate_y - previous_y)
        if movement_distance <= radius:
            local_candidates.append((candidate_x, candidate_y, float(candidate["distance"])))

    if len(local_candidates) < 2:
        return None

    weighted_x = 0.0
    weighted_y = 0.0
    total_weight = 0.0

    for candidate_x, candidate_y, rssi_distance in local_candidates:
        weight = 1 / max(rssi_distance, 0.5) ** 2
        weighted_x += candidate_x * weight
        weighted_y += candidate_y * weight
        total_weight += weight

    return weighted_x / total_weight, weighted_y / total_weight
