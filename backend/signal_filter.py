from collections import deque
from statistics import median


RSSI_COLUMNS = ("rssi_a", "rssi_b", "rssi_c", "rssi_d")


class RssiMedianFilter:
    def __init__(self, window_size=3):
        if window_size < 1:
            raise ValueError("window_size must be at least 1.")

        self.history = {
            column: deque(maxlen=window_size)
            for column in RSSI_COLUMNS
        }

    def apply(self, scan):
        filtered = dict(scan)
        carried = _carried_set(scan.get("carried"))

        for column in RSSI_COLUMNS:
            value = _parse_number(scan.get(column))

            if column not in carried and value is not None:
                self.history[column].append(value)

            if self.history[column]:
                filtered[column] = _format_number(median(self.history[column]))
            elif value is not None:
                filtered[column] = _format_number(value)

        return filtered


def _carried_set(value):
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    return {str(item) for item in value}


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


def _format_number(value):
    if float(value).is_integer():
        return int(value)

    return float(value)
