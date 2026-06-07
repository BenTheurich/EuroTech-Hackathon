from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

from knn_model import WifiKNNLocalizer
from location_tracker import LocationTracker
from pathfinding import find_route

app = FastAPI()

# Allow frontend React app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

localizer = WifiKNNLocalizer()
tracker = LocationTracker()


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
        predicted_location = localizer.predict_location_details(data)
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
