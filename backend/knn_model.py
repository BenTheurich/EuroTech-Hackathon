import csv
from pathlib import Path
from statistics import mean

import numpy as np
from sklearn.neighbors import KNeighborsRegressor


FEATURE_COLUMNS = ("rssi_a", "rssi_b", "rssi_c", "rssi_d")
TARGET_COLUMNS = ("x", "y")
MAX_CANDIDATES = 12
AMBIGUITY_DISTANCE_DELTA = 2.0
AMBIGUITY_SPREAD_THRESHOLD_M = 2.0


class WifiKNNLocalizer:
    def __init__(
        self,
        fingerprint_path=None,
        fallback_path=None,
        data_dir=None,
        n_neighbors=3,
        aggregate_by_point=True,
    ):
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

        self.raw_training_count = len(features)
        if aggregate_by_point:
            features, targets = self._aggregate_by_point(features, targets)

        self.training_count = len(features)
        effective_neighbors = min(self.n_neighbors, self.training_count)
        self.targets_array = np.array(targets, dtype=float)

        self.model = KNeighborsRegressor(
            n_neighbors=effective_neighbors,
            weights="distance",
        )
        self.model.fit(
            np.array(features, dtype=float),
            self.targets_array,
        )

    def predict_location(self, scan):
        prediction = self.predict_location_details(scan)

        return {
            "x": prediction["x"],
            "y": prediction["y"],
        }

    def predict_location_details(self, scan):
        feature_vector = self._scan_to_features(scan)
        features = np.array([feature_vector], dtype=float)
        prediction = self.model.predict(features)[0]
        candidate_count = min(MAX_CANDIDATES, self.training_count)
        distances, indices = self.model.kneighbors(features, n_neighbors=candidate_count)
        nearest_distance = float(distances[0][0])
        candidates = [
            {
                "x": float(self.targets_array[index][0]),
                "y": float(self.targets_array[index][1]),
                "distance": float(distance),
            }
            for distance, index in zip(distances[0], indices[0])
        ]

        return {
            "x": float(prediction[0]),
            "y": float(prediction[1]),
            "knn_x": float(prediction[0]),
            "knn_y": float(prediction[1]),
            "nearest_distance": nearest_distance,
            "candidates": candidates,
            "ambiguity": _candidate_ambiguity(candidates, nearest_distance),
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

    @staticmethod
    def _aggregate_by_point(features, targets):
        grouped = {}

        for feature_row, target_row in zip(features, targets):
            point = tuple(target_row)
            grouped.setdefault(point, []).append(feature_row)

        aggregated_features = []
        aggregated_targets = []

        for point in sorted(grouped):
            rows = grouped[point]
            aggregated_features.append([
                mean(column_values)
                for column_values in zip(*rows)
            ])
            aggregated_targets.append(list(point))

        return aggregated_features, aggregated_targets

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


def _candidate_ambiguity(candidates, nearest_distance):
    close_candidates = [
        candidate
        for candidate in candidates
        if float(candidate["distance"]) <= nearest_distance + AMBIGUITY_DISTANCE_DELTA
    ]

    spread = 0.0
    for index, candidate in enumerate(close_candidates):
        for other in close_candidates[index + 1:]:
            spread = max(
                spread,
                _candidate_distance(candidate, other),
            )

    return {
        "spread_m": round(spread, 2),
        "ambiguous": spread >= AMBIGUITY_SPREAD_THRESHOLD_M,
    }


def _candidate_distance(candidate, other):
    return float(
        np.hypot(
            float(candidate["x"]) - float(other["x"]),
            float(candidate["y"]) - float(other["y"]),
        )
    )
