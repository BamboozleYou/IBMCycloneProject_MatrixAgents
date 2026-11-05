"""Load and validate cyclone CSV data.

Usage:
    from ingestion.load import load_cyclones
    df = load_cyclones()          # loads default sample CSV
    df = load_cyclones("path/to/custom.csv")
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_DEFAULT_CSV = Path(__file__).resolve().parent.parent / "data" / "sample" / "cyclones.csv"

# Required columns and their expected Python types (post-cast)
_SCHEMA: dict[str, type] = {
    "cyclone_id": str,
    "name": str,
    "year": int,
    "basin": str,
    "category": str,
    "max_wind_kmh": float,
    "min_pressure_hpa": float,
    "landfall_region": str,
    "landfall_lat": float,
    "landfall_lon": float,
    "duration_days": int,
    "deaths": int,
    "displaced_thousands": float,
    "damage_usd_millions": float,
    "label": str,
}

_VALID_LABELS = {"mild", "moderate", "severe"}


class ValidationError(ValueError):
    """Raised when a row fails schema or domain validation."""


@dataclass
class CycloneRecord:
    cyclone_id: str
    name: str
    year: int
    basin: str
    category: str
    max_wind_kmh: float
    min_pressure_hpa: float
    landfall_region: str
    landfall_lat: float
    landfall_lon: float
    duration_days: int
    deaths: int
    displaced_thousands: float
    damage_usd_millions: float
    label: str
    extra: dict[str, Any] = field(default_factory=dict)


def _cast_row(row: dict[str, str], row_num: int) -> dict[str, Any]:
    """Cast raw CSV strings to typed values per _SCHEMA."""
    result: dict[str, Any] = {}
    for col, typ in _SCHEMA.items():
        raw = row.get(col, "").strip()
        if raw == "":
            raise ValidationError(f"Row {row_num}: missing required column '{col}'")
        try:
            result[col] = typ(raw)
        except (ValueError, TypeError) as exc:
            raise ValidationError(
                f"Row {row_num}: column '{col}' cannot be cast to {typ.__name__} (got {raw!r})"
            ) from exc
    # Capture any extra columns
    result["extra"] = {k: v for k, v in row.items() if k not in _SCHEMA}
    return result


def _validate_domain(record: dict[str, Any], row_num: int) -> None:
    """Apply domain-level constraints."""
    if record["year"] < 1900 or record["year"] > 2100:
        raise ValidationError(f"Row {row_num}: year {record['year']} out of plausible range")
    if not (0 < record["max_wind_kmh"] < 500):
        raise ValidationError(f"Row {row_num}: max_wind_kmh {record['max_wind_kmh']} out of range")
    if not (850 < record["min_pressure_hpa"] < 1050):
        raise ValidationError(f"Row {row_num}: min_pressure_hpa {record['min_pressure_hpa']} out of range")
    if not (-90 <= record["landfall_lat"] <= 90):
        raise ValidationError(f"Row {row_num}: landfall_lat {record['landfall_lat']} invalid")
    if not (-180 <= record["landfall_lon"] <= 180):
        raise ValidationError(f"Row {row_num}: landfall_lon {record['landfall_lon']} invalid")
    if record["label"] not in _VALID_LABELS:
        raise ValidationError(
            f"Row {row_num}: label {record['label']!r} not in {_VALID_LABELS}"
        )


def load_cyclones(path: str | Path | None = None) -> list[CycloneRecord]:
    """Load, validate, and return cyclone records from *path*.

    Args:
        path: CSV file path. Defaults to ``data/sample/cyclones.csv``.

    Returns:
        List of validated :class:`CycloneRecord` objects.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValidationError: If any row fails type or domain checks.
    """
    csv_path = Path(path) if path is not None else _DEFAULT_CSV
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    records: list[CycloneRecord] = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        # Validate header
        missing_cols = set(_SCHEMA) - set(reader.fieldnames or [])
        if missing_cols:
            raise ValidationError(f"CSV missing columns: {sorted(missing_cols)}")

        for row_num, row in enumerate(reader, start=2):  # row 1 = header
            typed = _cast_row(row, row_num)
            _validate_domain(typed, row_num)
            extra = typed.pop("extra")
            records.append(CycloneRecord(**typed, extra=extra))

    if not records:
        raise ValidationError("CSV is empty — no data rows found")

    return records
