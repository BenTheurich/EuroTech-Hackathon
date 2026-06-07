from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import json
import os

from anchor_hints import apply_anchor_hint, detect_anchor_hint
from knn_model import WifiKNNLocalizer
from location_tracker import LocationTracker
from pathfinding import find_route
from signal_filter import RssiMedianFilter, RSSI_COLUMNS

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

# Allow frontend React app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_localizer():
    return WifiKNNLocalizer(
        fingerprint_path=_configured_fingerprint_path(),
        n_neighbors=_configured_knn_neighbors(),
    )


# The live demo runs in the 7x5 m room captured in fingerprints1400.csv
# (10 scans/point, ~1.8 m median CV error). The cleaned version imputes the
# few missing-anchor gaps. Override with WIFI_FINGERPRINT_PATH if needed.
DEFAULT_FINGERPRINT_PATH = os.path.join(PROJECT_ROOT, "data", "fingerprints1400_clean.csv")


def _configured_fingerprint_path():
    fingerprint_path = os.environ.get("WIFI_FINGERPRINT_PATH")
    if not fingerprint_path:
        return DEFAULT_FINGERPRINT_PATH

    if os.path.isabs(fingerprint_path):
        return fingerprint_path

    return os.path.join(PROJECT_ROOT, fingerprint_path)


def _configured_knn_neighbors():
    value = os.environ.get("WIFI_KNN_NEIGHBORS")
    if not value:
        return 3

    try:
        neighbors = int(value)
    except ValueError as error:
        raise ValueError("WIFI_KNN_NEIGHBORS must be a positive integer.") from error

    if neighbors < 1:
        raise ValueError("WIFI_KNN_NEIGHBORS must be a positive integer.")

    return neighbors


def _configured_filter_window():
    # The live RSSI is noisy (~4-6 dBm between adjacent points), so we median
    # several scans together. Larger = steadier dot but more lag while walking.
    # Tune live during the demo via WIFI_FILTER_WINDOW without editing code.
    value = os.environ.get("WIFI_FILTER_WINDOW")
    if not value:
        return 3

    try:
        window = int(value)
    except ValueError as error:
        raise ValueError("WIFI_FILTER_WINDOW must be a positive integer.") from error

    if window < 1:
        raise ValueError("WIFI_FILTER_WINDOW must be a positive integer.")

    return window


localizer = create_localizer()
tracker = LocationTracker()
signal_filter = RssiMedianFilter(window_size=_configured_filter_window())


# ==========================================
# 2. WEBSOCKET MANAGER
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# ==========================================
# 3. API ENDPOINTS
# ==========================================

@app.post("/api/location-data")
async def receive_scan(data: dict):
    """
    The Python script on the laptop POSTs data here every 1 second.
    Expected payload: {"rssi_a": -50, "rssi_b": -60, "rssi_c": -70, "rssi_d": -65}
    """
    try:
        filtered_scan = signal_filter.apply(data)
        predicted_location = localizer.predict_location_details(filtered_scan)
        anchor_hint = detect_anchor_hint(filtered_scan, predicted_location)
        predicted_location = apply_anchor_hint(predicted_location, anchor_hint)
        predicted_location["filtered_rssi"] = {
            key: filtered_scan.get(key)
            for key in RSSI_COLUMNS
        }
        payload_data = tracker.update(predicted_location, data)

        # Create the payload for the React Frontend
        payload = json.dumps(payload_data)

        # Broadcast the new coordinates to the React Dashboard
        await manager.broadcast(payload)

        return {
            "status": "success",
            "predicted_location": payload_data,
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/route")
async def compute_route(request: dict):
    """Dijkstra route from the visitor's live location to their destination.

    The React frontend POSTs the user's current position, the destination POI
    they picked, and the floor walls it is drawing:

        {
          "start": {"x": 3.2, "y": 1.7},
          "goal":  {"x": 6.4, "y": 4.4},
          "walls": ["h-0-0", "v-2-3", ...],   # optional, defaults to venue floor
          "preference": "fastest"             # optional
        }

    Returns the route as a poly-line in the shared grid coordinate space so the
    map can draw it directly (see pathfinding.find_route).
    """
    try:
        start = request.get("start")
        goal = request.get("goal")
        if not start or not goal:
            return {"status": "error", "message": "Both 'start' and 'goal' are required."}

        route = find_route(
            start,
            goal,
            walls=request.get("walls"),
            preference=request.get("preference", "fastest"),
        )
        return {"status": "success", **route}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/playback")
async def playback_position(data: dict):
    """Demo playback channel: broadcast a hand-authored (x, y) straight to the map.

    This deliberately BYPASSES the KNN localizer and the LocationTracker. Those
    exist to denoise real, noisy Wi-Fi localization; feeding them a clean,
    hand-crafted path produces jerky, lagging output (the deadband/hysteresis
    fights smooth motion). For a prerecorded "look how it walks the map" demo we
    want the dot to follow the authored path exactly, so we emit the position as
    a finished payload in the same shape the tracker would.

    Used by scanner/simulate_reception_walk.py. The live positioning path
    (scanner -> /api/location-data -> KNN -> tracker) is untouched.
    """
    try:
        x = float(data["x"])
        y = float(data["y"])
    except (KeyError, TypeError, ValueError):
        return {"status": "error", "message": "Both numeric 'x' and 'y' are required."}

    payload_data = {
        "x": round(x, 2),
        "y": round(y, 2),
        "raw_x": round(float(data.get("raw_x", x)), 2),
        "raw_y": round(float(data.get("raw_y", y)), 2),
        "knn_x": round(x, 2),
        "knn_y": round(y, 2),
        "confidence": round(float(data.get("confidence", 1.0)), 2),
        "status": data.get("status", "live"),
        "nearest_distance": data.get("nearest_distance"),
        "filtered_rssi": None,
        "anchor_hint": None,
        "ambiguity": {"spread_m": 0.0, "ambiguous": False},
        "held": False,
        "scan_age_ms": int(data.get("scan_age_ms", 0)),
        "carried": data.get("carried", []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "playback": True,
    }
    await manager.broadcast(json.dumps(payload_data))
    return {"status": "success", "predicted_location": payload_data}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    The React frontend connects here to receive live X,Y updates.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
