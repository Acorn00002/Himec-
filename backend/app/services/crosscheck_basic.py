"""Deterministic cross-check comparison logic.

This module intentionally contains no LLM calls. Given the raw ParameterValue rows
extracted for one piece of equipment, it groups them by parameter name and decides
whether the values reported across documents agree (accounting for unit conversion),
producing the ✓ / ⚠ status shown in the CrossCheck table. Severity, root-cause reasoning
and impact analysis are judgment calls that belong to the rule+LLM layer (see
services/ai/llm_client.py) — this module only answers "do these numbers agree".
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from app.services.parameters import canonical_key, label as parameter_label, normalize_unit

# unit -> (dimension, multiplier to the dimension's base unit)
UNIT_FACTORS: dict[str, tuple[str, float]] = {
    "W": ("power", 1.0),
    "kW": ("power", 1_000.0),
    "MW": ("power", 1_000_000.0),
    "HP": ("power", 745.7),
    "V": ("voltage", 1.0),
    "kV": ("voltage", 1_000.0),
    "A": ("current", 1.0),
    "mA": ("current", 0.001),
    "rpm": ("rpm", 1.0),
    "RPM": ("rpm", 1.0),
    "%": ("ratio", 1.0),
    "mm": ("length", 1.0),
    "cm": ("length", 10.0),
    "m": ("length", 1_000.0),
    "mm2": ("cable_area", 1.0),
    "mm²": ("cable_area", 1.0),
    "kg": ("weight", 1.0),
    "ton": ("weight", 1_000.0),
    "bar": ("pressure", 1.0),
    "kPa": ("pressure", 0.01),
    "MPa": ("pressure", 10.0),
    "m3/h": ("flow", 1.0),
    "L/min": ("flow", 0.06),
    "C": ("temperature", 1.0),
    "°C": ("temperature", 1.0),
}

RELATIVE_TOLERANCE = 0.01  # 1% — accounts for rounding, not a real discrepancy


@dataclass
class SourceValue:
    document_id: int
    document_name: str
    value: str
    unit: str | None
    location: str | None = None
    raw_snippet: str | None = None
    numeric_value: float | None = None


@dataclass
class ParameterComparison:
    name: str  # Korean display label (e.g. "정격출력") — for the UI
    sources: list[SourceValue]
    status: str  # "match" | "mismatch"
    reason: str | None = field(default=None)
    kind: str | None = field(default=None)  # "dimension_mismatch" | "deviation_mismatch" | "text_mismatch"
    deviation: float | None = field(default=None)  # max relative deviation, only set for deviation_mismatch
    key: str = field(default="")  # canonical key (e.g. "Power") — for the deterministic rule tables


def _to_base(unit: str | None, numeric_value: float | None) -> tuple[str | None, float | None]:
    if unit is None or numeric_value is None:
        return None, None
    factor = UNIT_FACTORS.get(unit)
    if factor is None:
        return unit, numeric_value
    dimension, multiplier = factor
    return dimension, numeric_value * multiplier


def compare_parameter(name: str, sources: list[SourceValue]) -> ParameterComparison:
    if len(sources) <= 1:
        return ParameterComparison(name=name, sources=sources, status="match")

    numeric_sources = [s for s in sources if s.numeric_value is not None]

    if len(numeric_sources) == len(sources):
        dimensions = set()
        base_values = []
        for s in numeric_sources:
            dim, base_val = _to_base(s.unit, s.numeric_value)
            dimensions.add(dim)
            base_values.append(base_val)

        if len(dimensions) > 1:
            return ParameterComparison(
                name=name, sources=sources, status="mismatch",
                reason="문서마다 단위 체계가 달라 직접 비교할 수 없습니다.",
                kind="dimension_mismatch",
            )

        mean = sum(base_values) / len(base_values)
        if mean == 0:
            max_dev = max(abs(v) for v in base_values)
        else:
            max_dev = max(abs(v - mean) / abs(mean) for v in base_values)

        if max_dev <= RELATIVE_TOLERANCE:
            return ParameterComparison(name=name, sources=sources, status="match")
        return ParameterComparison(
            name=name, sources=sources, status="mismatch",
            reason=f"문서 간 값 편차가 {max_dev * 100:.1f}%로 허용 오차(1%)를 초과합니다.",
            kind="deviation_mismatch", deviation=max_dev,
        )

    # non-numeric (text) comparison, e.g. manufacturer / model
    normalized = {s.value.strip().lower() for s in sources}
    if len(normalized) == 1:
        return ParameterComparison(name=name, sources=sources, status="match")
    return ParameterComparison(
        name=name, sources=sources, status="mismatch",
        reason="문서 간 값이 서로 다릅니다.",
        kind="text_mismatch",
    )


def build_parameter_rows(
    parameter_values: list,  # list[app.db.models.ParameterValue] with .document loaded
) -> list[ParameterComparison]:
    grouped: dict[str, list[SourceValue]] = defaultdict(list)
    for pv in parameter_values:
        grouped[canonical_key(pv.name)].append(
            SourceValue(
                document_id=pv.document_id,
                document_name=pv.document.filename,
                value=pv.value,
                unit=normalize_unit(pv.unit),
                location=pv.location,
                raw_snippet=pv.raw_snippet,
                numeric_value=pv.numeric_value,
            )
        )

    comparisons = []
    for key, sources in grouped.items():
        comparison = compare_parameter(key, sources)
        comparison.key = key
        comparison.name = parameter_label(key)
        comparisons.append(comparison)
    return comparisons
