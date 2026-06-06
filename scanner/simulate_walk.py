"""
Fake Wi-Fi scanner for development.

Use this when you do NOT have the 4 phone hotspots or a Windows laptop handy
but still want to see the live map move. It pretends a person is walking a
loop around the room, converts their position into believable RSSI values for
the 4 anchors, and POSTs them to the backend exactly like the real scanner.

Run it from anywhere (Windows, Mac, Linux, WSL):

    python scanner/simulate_walk.py

Requires only `requests` (pip install requests). The backend must be running.
"""

import math
import time

import requests


BACKEND_URL = "http://localhost:8000/api/location-data"

# Seconds between fake scans. The real scanner is ~3s; we go faster so the
# frontend dev sees smooth movement while building.
STEP_SECONDS = 0.7

# Anchor reference positions, in the SAME coordinate space as the fingerprint
# data the KNN is trained on: the 7 m x 5 m fingerprint grid.
ROOM_WIDTH = 7.0
ROOM_HEIGHT = 5.0
ANCHOR_POSITIONS = {
    "rssi_a": (0.0, 0.0),
    "rssi_b": (ROOM_WIDTH, 0.0),
    "rssi_c": (0.0, ROOM_HEIGHT),
    "rssi_d": (ROOM_WIDTH, ROOM_HEIGHT),
}

# Signal model: dBm at the anchor itself, and how fast it weakens with distance.
RSSI_AT_ZERO_DISTANCE = -40.0
RSSI_PER_METER = -10.0
RSSI_FLOOR = -90.0


def position_at(t):
    """A smooth looping path around the middle of the room (a circle)."""
    center_x = ROOM_WIDTH / 2.0
    center_y = ROOM_HEIGHT / 2.0
    x = center_x + (ROOM_WIDTH / 3.0) * math.cos(t)
    y = center_y + (ROOM_HEIGHT / 3.0) * math.sin(t)
    return x, y


def rssi_from_position(x, y):
    """Turn a walker position into one RSSI value per anchor."""
    scan = {}

    for anchor_key, (ax, ay) in ANCHOR_POSITIONS.items():
        distance = math.hypot(x - ax, y - ay)
        rssi = RSSI_AT_ZERO_DISTANCE + RSSI_PER_METER * distance
        scan[anchor_key] = round(max(RSSI_FLOOR, rssi), 1)

    return scan


def main():
    print("Simulated walker started. Posting fake scans to:")
    print(f"  {BACKEND_URL}")
    print("Press CTRL + C to stop.\n")

    t = 0.0

    while True:
        try:
            x, y = position_at(t)
            scan = rssi_from_position(x, y)

            response = requests.post(BACKEND_URL, json=scan, timeout=2)

            if response.status_code == 200:
                predicted = response.json().get("predicted_location")
                print(
                    f"walker=({x:.2f}, {y:.2f}) "
                    f"scan={scan} -> backend predicted {predicted}"
                )
            else:
                print(f"Backend returned {response.status_code}: {response.text}")

            t += 0.15
            time.sleep(STEP_SECONDS)

        except KeyboardInterrupt:
            print("\nSimulator stopped by user.")
            break
        except requests.exceptions.ConnectionError:
            print("Could not reach backend. Is it running on port 8000?")
            time.sleep(2)


if __name__ == "__main__":
    main()
