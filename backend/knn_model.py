import csv
from pathlib import Path

import numpy as np
from sklearn.neighbors import KNeighborsRegressor


FEATURE_COLUMNS = ("rssi_a", "rssi_b", "rssi_c", "rssi_d")
TARGET_COLUMNS = ("x", "y")


class WifiKNNLocalizer:
    def __init__(self, fingerprint_path=None, fallback_path=None, data_dir=None, n_neighbors=3):
        if n_neighbors < 1:
            raise ValueError("n_neighbors must be at least 1.")

        project_root = Path(__file__).resolve().parent.parent
        data_dir = Path(data_dir or project_root / "data")
        self.n_neighbors = n_neighbors
        self.training_paths = self._training_paths(
            data_dir,
            fingerprint_path,
            fallback_path,
        )

        self.training_source = self._choose_training_source()
        features, targets = self._load_fingerprints(self.training_source)

        if not features:
            raise ValueError(f"No complete fingerprint rows found in {self.training_source}.")

        self.training_count = len(features)
        effective_neighbors = min(self.n_neighbors, self.training_count)

        self.model = KNeighborsRegressor(
            n_neighbors=effective_neighbors,
            weights="distance",
        )
        self.model.fit(
            np.array(features, dtype=float),
            np.array(targets, dtype=float),
        )

    def predict_location(self, scan):
        feature_vector = self._scan_to_features(scan)
        prediction = self.model.predict(np.array([feature_vector], dtype=float))[0]

        return {
            "x": float(prediction[0]),
            "y": float(prediction[1]),
        }

    def _choose_training_source(self):
        for path in self.training_paths:
            if path.exists():
                return path

        raise FileNotFoundError(
            "No fingerprint data found at any of: "
            + ", ".join(str(path) for path in self.training_paths)
        )

    @staticmethod
    def _training_paths(data_dir, fingerprint_path, fallback_path):
        if fingerprint_path is not None:
            return [Path(fingerprint_path)]

        return [
            data_dir / "fingerprints_clean.csv",
            data_dir / "fingerprints.csv",
            Path(fallback_path or data_dir / "sample_fingerprints.csv"),
        ]

    def _load_fingerprints(self, path):
        features = []
        targets = []

        with path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                feature_row = [self._parse_number(row.get(column)) for column in FEATURE_COLUMNS]
                target_row = [self._parse_number(row.get(column)) for column in TARGET_COLUMNS]

                if any(value is None for value in feature_row + target_row):
                    continue

                features.append(feature_row)
                targets.append(target_row)

        return features, targets

    def _scan_to_features(self, scan):
        values = []

        for column in FEATURE_COLUMNS:
            value = self._parse_number(scan.get(column))

            if value is None:
                raise ValueError(f"Live scan is missing a numeric {column} value.")

            values.append(value)

        return values

    @staticmethod
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
