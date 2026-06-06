import json
import asyncio
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parent))

import main


class FakeLocalizer:
    def predict_location_details(self, data):
        return {"x": 1.25, "y": 2.5, "nearest_distance": 5.0}


class FakeTracker:
    def update(self, prediction, data):
        return {
            "x": 1.25,
            "y": 2.5,
            "raw_x": prediction["x"],
            "raw_y": prediction["y"],
            "confidence": 0.94,
            "status": "live",
            "nearest_distance": prediction["nearest_distance"],
            "scan_age_ms": 10,
            "carried": data["carried"],
            "timestamp": "2026-06-06T12:00:00+00:00",
        }


class FakeManager:
    def __init__(self):
        self.messages = []

    async def broadcast(self, message):
        self.messages.append(message)


def test_receive_scan_broadcasts_expanded_location_payload(monkeypatch):
    fake_manager = FakeManager()
    monkeypatch.setattr(main, "localizer", FakeLocalizer())
    monkeypatch.setattr(main, "tracker", FakeTracker())
    monkeypatch.setattr(main, "manager", fake_manager)

    response = asyncio.run(
        main.receive_scan(
            {
                "rssi_a": -50,
                "rssi_b": -60,
                "rssi_c": -70,
                "rssi_d": -80,
                "carried": ["rssi_b"],
            }
        )
    )

    broadcast = json.loads(fake_manager.messages[0])
    assert response["status"] == "success"
    assert set(broadcast) == {
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
    assert broadcast["carried"] == ["rssi_b"]
