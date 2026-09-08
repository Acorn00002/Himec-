"""Deterministic engineering calculation checks (spec section 3-1 / 7-F).

These are NOT cross-document comparisons (see crosscheck_basic.py for that) — they
check whether a single equipment's reported values are internally consistent with
standard electrical engineering formulas. Every formula here is a textbook relation;
nothing is inferred or guessed by an LLM, and a check only runs when every input value
it needs was actually extracted from a document.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.db import models
from app.services.parameters import canonical_key

DEFAULT_POWER_FACTOR = 0.85
DEFAULT_EFFICIENCY = 0.90
CURRENT_TOLERANCE = 0.15  # 15% — beyond this, the reported current doesn't match P/V
BREAKER_MIN_MARGIN = 1.15  # standard minimum margin for motor branch-circuit protection
BREAKER_MAX_MARGIN = 3.0   # beyond this the breaker is unusually oversized for the load

POWER_UNIT_TO_W = {"W": 1, "kW": 1_000, "MW": 1_000_000, "HP": 745.7}
VOLTAGE_UNIT_TO_V = {"V": 1, "kV": 1_000}
CURRENT_UNIT_TO_A = {"A": 1, "mA": 0.001}


@dataclass
class CalcFinding:
    check: str  # "current_vs_power" | "breaker_undersized" | "breaker_oversized"
    title: str
    message: str
    calculated_value: float
    reported_value: float
    unit: str
    severity: str
    impact_items: list[str]
    inputs: list[models.ParameterValue]  # the ParameterValue rows the calc used, for evidence


def _representative(parameter_values: list[models.ParameterValue], name: str) -> models.ParameterValue | None:
    """First document that reports a numeric value for this parameter. Deliberately
    simple (not an average) so evidence can point at one real source document."""
    for pv in parameter_values:
        if canonical_key(pv.name) == name and pv.numeric_value is not None:
            return pv
    return None


def check_current_consistency(parameter_values: list[models.ParameterValue]) -> CalcFinding | None:
    power = _representative(parameter_values, "Power")
    voltage = _representative(parameter_values, "Voltage")
    current = _representative(parameter_values, "Current")
    if not (power and voltage and current):
        return None

    power_w = power.numeric_value * POWER_UNIT_TO_W.get(power.unit or "W", 1)
    voltage_v = voltage.numeric_value * VOLTAGE_UNIT_TO_V.get(voltage.unit or "V", 1)
    current_a = current.numeric_value * CURRENT_UNIT_TO_A.get(current.unit or "A", 1)
    if voltage_v <= 0:
        return None

    pf_row = _representative(parameter_values, "Power Factor")
    pf_value = pf_row.numeric_value if pf_row else DEFAULT_POWER_FACTOR
    eff_row = _representative(parameter_values, "Efficiency")
    eff_value = DEFAULT_EFFICIENCY
    if eff_row:
        eff_value = eff_row.numeric_value / 100 if eff_row.numeric_value > 1 else eff_row.numeric_value

    calculated_current = power_w / (math.sqrt(3) * voltage_v * pf_value * eff_value)
    if calculated_current <= 0:
        return None

    deviation = abs(calculated_current - current_a) / calculated_current
    if deviation <= CURRENT_TOLERANCE:
        return None

    inputs = [power, voltage, current] + ([pf_row] if pf_row else []) + ([eff_row] if eff_row else [])
    return CalcFinding(
        check="current_vs_power",
        title="정격전류가 정격출력/정격전압 계산값과 차이가 있습니다",
        message=(
            f"정격출력({power.value}{power.unit})과 정격전압({voltage.value}{voltage.unit})으로 3상 기준 계산한 "
            f"예상 전류는 약 {calculated_current:.1f} A입니다 (역률 {pf_value:.2f}, 효율 {eff_value * 100:.0f}% "
            f"{'문서 값' if eff_row else '가정값'} 적용). 문서에 기재된 전류 {current_a:.1f} A와 "
            f"{deviation * 100:.0f}% 차이가 있어 허용 오차({CURRENT_TOLERANCE * 100:.0f}%)를 초과합니다."
        ),
        calculated_value=round(calculated_current, 2),
        reported_value=current_a,
        unit="A",
        severity="MEDIUM",
        impact_items=["케이블 규격 산정", "차단기 선정", "부하 계산"],
        inputs=inputs,
    )


def check_breaker_sizing(parameter_values: list[models.ParameterValue]) -> CalcFinding | None:
    breaker = _representative(parameter_values, "Breaker Size")
    current = _representative(parameter_values, "Current")
    if not (breaker and current):
        return None

    breaker_a = breaker.numeric_value * CURRENT_UNIT_TO_A.get(breaker.unit or "A", 1)
    current_a = current.numeric_value * CURRENT_UNIT_TO_A.get(current.unit or "A", 1)
    if current_a <= 0:
        return None

    ratio = breaker_a / current_a
    inputs = [breaker, current]

    if ratio < BREAKER_MIN_MARGIN:
        return CalcFinding(
            check="breaker_undersized",
            title="차단기 용량이 정격전류 대비 부족할 수 있습니다",
            message=(
                f"차단기 용량({breaker_a:.0f} A)이 정격전류({current_a:.1f} A)의 {ratio:.2f}배로, "
                f"일반적인 여유율 기준(최소 {BREAKER_MIN_MARGIN}배) 미만입니다. 과전류 보호 여유가 부족할 수 있습니다."
            ),
            calculated_value=round(current_a * BREAKER_MIN_MARGIN, 1),
            reported_value=breaker_a,
            unit="A",
            severity="HIGH",
            impact_items=["차단기 선정", "보호 협조", "안전 규정 준수"],
            inputs=inputs,
        )
    if ratio > BREAKER_MAX_MARGIN:
        return CalcFinding(
            check="breaker_oversized",
            title="차단기 용량이 정격전류 대비 과도하게 큽니다",
            message=(
                f"차단기 용량({breaker_a:.0f} A)이 정격전류({current_a:.1f} A)의 {ratio:.2f}배로 "
                f"통상적인 범위(최대 {BREAKER_MAX_MARGIN}배)를 초과합니다. 과전류 보호가 제대로 동작하지 않을 수 있습니다."
            ),
            calculated_value=round(current_a * BREAKER_MAX_MARGIN, 1),
            reported_value=breaker_a,
            unit="A",
            severity="LOW",
            impact_items=["보호 협조"],
            inputs=inputs,
        )
    return None


def run_calc_checks(parameter_values: list[models.ParameterValue]) -> list[CalcFinding]:
    findings = []
    for check_fn in (check_current_consistency, check_breaker_sizing):
        result = check_fn(parameter_values)
        if result:
            findings.append(result)
    return findings
