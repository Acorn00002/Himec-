"""Deterministic severity + impact rules (section 8/9 of the product spec).

Severity is never decided by the LLM alone: it comes from a fixed parameter category
plus the measured deviation size (both computed in crosscheck_basic). The LLM (see
services/ai/issue_reasoning.py) is only allowed to *explain* a severity that this
module already decided, never to change it.
"""

from __future__ import annotations

# Parameters whose mismatch directly drives electrical protection/sizing decisions.
HIGH_BASE_PARAMS = {"Power", "Voltage", "Current", "Breaker Size", "Cable Size"}
# Parameters that identify *which* equipment/spec is correct, or size mechanical flow.
MEDIUM_BASE_PARAMS = {"Model", "Manufacturer", "Flow", "Pressure"}
# Everything else (RPM, Efficiency, Power Factor, Temperature, Dimension, Weight, ...) -> LOW baseline.

HIGH_DEVIATION_THRESHOLD = 0.5   # >=50% off -> HIGH regardless of category (e.g. unit/digit errors)
MEDIUM_DEVIATION_THRESHOLD = 0.05  # >=5% off escalates a HIGH-category param from MEDIUM to HIGH

ISSUE_TYPE_BY_KIND = {
    "dimension_mismatch": "unit_mismatch",
    "deviation_mismatch": "value_mismatch",
    "text_mismatch": "spec_mismatch",
}

IMPACT_MAP: dict[str, list[str]] = {
    "Power": ["케이블 규격 산정", "차단기 선정", "부하 계산", "배전반 용량"],
    "Voltage": ["케이블 절연 등급", "전동기 기동방식 선정"],
    "Current": ["차단기 선정", "케이블 규격 산정"],
    "Breaker Size": ["배전반 용량", "보호 협조"],
    "Cable Size": ["전압 강하 계산", "전선관 규격 산정"],
    "Model": ["예비품 조달", "정비 매뉴얼 참조", "성능 곡선 확인"],
    "Manufacturer": ["예비품 조달", "벤더 데이터시트 참조"],
    "Flow": ["펌프/팬 용량 산정", "배관 규격 산정"],
    "Pressure": ["펌프 용량 산정", "배관 압력 등급"],
    "RPM": ["커플링 선정", "벨트/풀리 산정"],
    "Efficiency": ["에너지 효율 검증", "부하 계산 정확도"],
    "Power Factor": ["콘덴서 뱅크 용량", "부하 계산 정확도"],
    "Temperature": ["절연 등급 확인"],
    "Dimension": ["배치/이격거리 검토"],
    "Weight": ["구조/양중 하중 검토"],
    "Frequency": ["전동기 회전수 확인", "인버터 설정"],
    "Insulation Class": ["절연 등급 확인", "허용 온도상승 확인"],
    "Protection Rating": ["설치 환경 적합성 확인"],
}
DEFAULT_IMPACT = ["설계 데이터 확인"]

# Parameters a given equipment_type is expected to report *somewhere* across its
# documents. Unrecognized equipment types are skipped entirely rather than guessing —
# a false "missing" flag is worse than staying silent (spec section 7-C).
REQUIRED_PARAMS_BY_TYPE: dict[str, list[str]] = {
    "Motor": ["Power", "Voltage", "RPM", "Efficiency"],
    "Pump": ["Flow", "Pressure", "Power"],
    "AHU": ["Power", "Flow"],
    "Fan": ["Power", "Flow"],
    "Compressor": ["Power", "Flow", "Pressure"],
    "Transformer": ["Power", "Voltage"],
}
MISSING_SEVERITY_OVERRIDE = {"Power": "MEDIUM", "Voltage": "MEDIUM"}


def missing_severity(parameter_name: str) -> str:
    return MISSING_SEVERITY_OVERRIDE.get(parameter_name, "LOW")


def issue_type_for(kind: str | None) -> str:
    return ISSUE_TYPE_BY_KIND.get(kind or "", "value_mismatch")


def decide_severity(parameter_name: str, kind: str | None, deviation: float | None) -> str:
    if kind == "dimension_mismatch":
        return "HIGH"
    if deviation is not None and deviation >= HIGH_DEVIATION_THRESHOLD:
        return "HIGH"
    if parameter_name in HIGH_BASE_PARAMS:
        if deviation is None or deviation >= MEDIUM_DEVIATION_THRESHOLD:
            return "HIGH"
        return "MEDIUM"
    if parameter_name in MEDIUM_BASE_PARAMS:
        return "MEDIUM"
    return "LOW"


def impact_items_for(parameter_name: str) -> list[str]:
    return IMPACT_MAP.get(parameter_name, DEFAULT_IMPACT)
