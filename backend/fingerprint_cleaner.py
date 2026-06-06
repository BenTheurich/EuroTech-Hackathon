import csv
import math
from pathlib import Path
from statistics import median


RSSI_COLUMNS = ("rssi_a", "rssi_b", "rssi_c", "rssi_d")
COORDINATE_COLUMNS = ("x", "y")


def clean_fingerprints(source_path, output_path):
    source_path = Path(source_path)
    output_path = Path(output_path)

    with source_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if not rows:
        raise ValueError(f"No fingerprint rows found in {source_path}.")

    missing_columns = [
        column
        for column in (*COORDINATE_COLUMNS, *RSSI_COLUMNS)
        if column not in fieldnames
    ]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    same_point_medians = _build_same_point_medians(rows)
    point_medians = _build_point_medians(rows)
    global_medians = _build_global_medians(rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_fieldnames = [
        *[name for name in fieldnames if not name.startswith("imputed_")],
        *[f"imputed_{column}" for column in RSSI_COLUMNS],
    ]

    imputed_counts = {column: 0 for column in RSSI_COLUMNS}
    cleaned_rows = []

    for row in rows:
        cleaned_row = {
            name: row.get(name, "")
            for name in output_fieldnames
            if not name.startswith("imputed_")
        }
        point = _point_key(row)

        for column in RSSI_COLUMNS:
            value = _parse_number(row.get(column))

            if value is None:
                value = _replacement_value(
                    point,
                    column,
                    same_point_medians,
                    point_medians,
                    global_medians,
                )
                cleaned_row[column] = _format_number(value)
                cleaned_row[f"imputed_{column}"] = "true"
                imputed_counts[column] += 1
            else:
                cleaned_row[column] = _format_number(value)
                cleaned_row[f"imputed_{column}"] = "false"

        cleaned_rows.append(cleaned_row)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    return {
        "rows": len(cleaned_rows),
        "output_path": str(output_path),
        "imputed": imputed_counts,
    }


def _replacement_value(point, column, same_point_medians, point_medians, global_medians):
    point_value = same_point_medians.get(point, {}).get(column)
    if point_value is not None:
        return point_value

    nearest_values = []
    for other_point, medians in sorted(point_medians.items()):
        if other_point == point:
            continue

        value = medians.get(column)
        if value is None:
            continue

        distance = math.dist(point, other_point)
        nearest_values.append((distance, other_point, value))

    if nearest_values:
        nearest_values.sort(key=lambda item: (item[0], item[1]))
        return median([value for _, _, value in nearest_values[:3]])

    global_value = global_medians.get(column)
    if global_value is None:
        raise ValueError(f"Cannot impute {column}; no values exist in the source data.")

    return global_value


def _build_same_point_medians(rows):
    grouped = {}

    for row in rows:
        point = _point_key(row)
        grouped.setdefault(point, {column: [] for column in RSSI_COLUMNS})

        for column in RSSI_COLUMNS:
            value = _parse_number(row.get(column))
            if value is not None:
                grouped[point][column].append(value)

    return {
        point: {
            column: median(values) if values else None
            for column, values in columns.items()
        }
        for point, columns in grouped.items()
    }


def _build_point_medians(rows):
    return _build_same_point_medians(rows)


def _build_global_medians(rows):
    values = {column: [] for column in RSSI_COLUMNS}

    for row in rows:
        for column in RSSI_COLUMNS:
            value = _parse_number(row.get(column))
            if value is not None:
                values[column].append(value)

    return {
        column: median(column_values) if column_values else None
        for column, column_values in values.items()
    }


def _point_key(row):
    return (_required_number(row, "x"), _required_number(row, "y"))


def _required_number(row, column):
    value = _parse_number(row.get(column))
    if value is None:
        raise ValueError(f"Fingerprint row is missing numeric {column}: {row}")
    return value


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
        return str(int(value))

    return f"{value:.2f}".rstrip("0").rstrip(".")
