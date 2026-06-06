import json
import asyncio
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parent))

import main


class FakeLocalizer:
    def __init__(self):
        self.last_data = None

    def predict_location_details(self, data):
        self.last_data = data
        return {
            "x": 1.25,
            "y": 2.5,
            "knn_x": 1.25,
            "knn_y": 2.5,
            "nearest_distance": 5.0,
            "candidates": [],
            "ambiguity": {"spread_m": 0.0, "ambiguous": False},
        }


class FakeTracker:
    def update(self, prediction, data):
        return {
            "x": 1.25,
            "y": 2.5,
            "raw_x": prediction["x"],
            "raw_y": prediction["y"],
            "knn_x": prediction["knn_x"],
            "knn_y": prediction["knn_y"],
            "confidence": 0.94,
            "status": "live",
            "nearest_distance": prediction["nearest_distance"],
            "filtered_rssi": prediction["filtered_rssi"],
            "anchor_hint": prediction["anchor_hint"],
            "ambiguity": prediction["ambiguity"],
            "held": False,
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
    fake_localizer = FakeLocalizer()
    monkeypatch.setattr(main, "localizer", fake_localizer)
    monkeypatch.setattr(main, "tracker", FakeTracker())
    monkeypatch.setattr(main, "manager", fake_manager)
    monkeypatch.setattr(main, "signal_filter", main.RssiMedianFilter())

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
    assert broadcast["carried"] == ["rssi_b"]
    assert broadcast["filtered_rssi"] == {
        "rssi_a": -50,
        "rssi_b": -60,
        "rssi_c": -70,
        "rssi_d": -80,
    }
    assert fake_localizer.last_data["rssi_a"] == -50


def test_create_localizer_uses_fingerprint_path_env(monkeypatch):
    class FakeWifiKNNLocalizer:
        def __init__(self, fingerprint_path=None, n_neighbors=1):
            self.fingerprint_path = fingerprint_path
            self.n_neighbors = n_neighbors

    monkeypatch.setattr(main, "WifiKNNLocalizer", FakeWifiKNNLocalizer)
    monkeypatch.setenv("WIFI_FINGERPRINT_PATH", "data/fingerprints_clean.csv")
    monkeypatch.setenv("WIFI_KNN_NEIGHBORS", "3")

    localizer = main.create_localizer()

    assert Path(localizer.fingerprint_path) == (
        Path(main.__file__).resolve().parent.parent / "data" / "fingerprints_clean.csv"
    )
    assert localizer.n_neighbors == 3


def test_configured_knn_neighbors_defaults_to_three(monkeypatch):
    monkeypatch.delenv("WIFI_KNN_NEIGHBORS", raising=False)

    assert main._configured_knn_neighbors() == 3


def test_configured_knn_neighbors_rejects_invalid_env(monkeypatch):
    monkeypatch.setenv("WIFI_KNN_NEIGHBORS", "0")

    try:
        main._configured_knn_neighbors()
    except ValueError as error:
        assert "WIFI_KNN_NEIGHBORS" in str(error)
    else:
        raise AssertionError("expected invalid KNN neighbor count to raise")
