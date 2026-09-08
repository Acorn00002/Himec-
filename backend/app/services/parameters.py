"""Canonical parameter & equipment-type registry.

Real design documents from different vendors/disciplines name the same quantity many
different ways — "Power", "정격출력", "출력", "Rated Output", "kW" — and the cross-check
only works if those all collapse to one row. This module is the single place that maps
any raw extracted name onto a stable canonical key plus a Korean display label.

Canonical keys stay in English on purpose: they are used as dict keys in the
deterministic rule tables (issue_rules, engineering_rules) and must not shift when the
UI language changes. Everything a user sees goes through `label()`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterDef:
    key: str
    label_ko: str
    aliases: tuple[str, ...]


# label_ko is what the UI shows. aliases are matched after normalization (see _norm):
# lower-cased, all spaces / underscores / hyphens / dots / middots removed. Include both
# Korean and English spellings, and bare-unit spellings ("kw") that documents sometimes
# use as a column header.
PARAMETER_DEFS: tuple[ParameterDef, ...] = (
    ParameterDef("Power", "정격출력", (
        "power", "ratedpower", "ratedoutput", "output", "motorpower", "motoroutput",
        "정격출력", "출력", "정격용량", "용량", "전동기출력", "축동력", "shaftpower", "kw", "kwrating",
    )),
    ParameterDef("Voltage", "정격전압", (
        "voltage", "ratedvoltage", "nominalvoltage", "operatingvoltage", "supplyvoltage",
        "정격전압", "전압", "사용전압", "공칭전압", "선간전압",
    )),
    ParameterDef("Current", "정격전류", (
        "current", "ratedcurrent", "fullloadcurrent", "fla", "loadcurrent", "amps", "amperage",
        "정격전류", "전류", "부하전류", "전부하전류",
    )),
    ParameterDef("RPM", "회전수", (
        "rpm", "speed", "rotationspeed", "rotationalspeed", "revmin", "revolutions",
        "회전수", "회전속도", "정격회전수", "극수rpm",
    )),
    ParameterDef("Efficiency", "효율", (
        "efficiency", "eff", "ratedefficiency", "motorefficiency", "ie",
        "효율", "정격효율", "전동기효율",
    )),
    ParameterDef("Power Factor", "역률", (
        "powerfactor", "pf", "cosphi", "cosφ", "cos", "displacementpowerfactor",
        "역률",
    )),
    ParameterDef("Cable Size", "케이블 규격", (
        "cablesize", "cable", "conductorsize", "conductorcsa", "cablecsa", "wiresize", "cablespec",
        "케이블규격", "케이블사이즈", "전선규격", "케이블굵기", "전선굵기", "케이블",
    )),
    ParameterDef("Breaker Size", "차단기 용량", (
        "breakersize", "breaker", "breakerrating", "mccb", "mcb", "cb", "trip", "tripsize",
        "차단기용량", "차단기", "차단기정격", "배선용차단기", "차단기규격",
    )),
    ParameterDef("Manufacturer", "제조사", (
        "manufacturer", "maker", "vendor", "brand", "supplier", "make",
        "제조사", "제작사", "제조업체", "메이커", "브랜드", "공급사",
    )),
    ParameterDef("Model", "모델명", (
        "model", "modelno", "modelnumber", "type", "typeno", "partnumber", "partno", "catalogno",
        "모델명", "모델", "형식", "형번", "품번", "형식번호",
    )),
    ParameterDef("Flow", "유량", (
        "flow", "flowrate", "capacity", "airflow", "waterflow", "cmh", "lpm", "gpm",
        "유량", "토출량", "풍량", "정격유량",
    )),
    ParameterDef("Pressure", "양정/압력", (
        "pressure", "head", "dischargepressure", "totalhead", "staticpressure", "designpressure",
        "압력", "양정", "토출압력", "정압", "전양정",
    )),
    ParameterDef("Temperature", "온도", (
        "temperature", "temp", "ambienttemperature", "designtemperature", "operatingtemperature",
        "온도", "사용온도", "주위온도", "설계온도",
    )),
    ParameterDef("Dimension", "외형치수", (
        "dimension", "dimensions", "size", "overallsize", "footprint",
        "외형치수", "치수", "크기", "외형", "규격",
    )),
    ParameterDef("Weight", "중량", (
        "weight", "mass", "drymass", "operatingweight", "shippingweight",
        "중량", "무게", "질량", "운전중량",
    )),
    ParameterDef("Frequency", "주파수", (
        "frequency", "freq", "hz", "ratedfrequency",
        "주파수", "정격주파수",
    )),
    ParameterDef("Insulation Class", "절연 등급", (
        "insulationclass", "insulation", "thermalclass", "insclass",
        "절연등급", "절연종", "절연",
    )),
    ParameterDef("Protection Rating", "보호 등급(IP)", (
        "protectionrating", "iprating", "ip", "enclosure", "enclosurerating", "protectiondegree",
        "보호등급", "방수방진등급", "외함보호등급",
    )),
)

def _norm(name: str) -> str:
    """Lower-case and strip separators / units-in-parens so aliases match loosely."""
    s = name.strip().lower()
    s = re.sub(r"\(.*?\)", "", s)  # drop "(kW)", "(3상)" etc.
    s = re.sub(r"[\s_\-.·/]+", "", s)
    return s


_KEY_TO_LABEL: dict[str, str] = {d.key: d.label_ko for d in PARAMETER_DEFS}
_ALIAS_TO_KEY: dict[str, str] = {}
for _d in PARAMETER_DEFS:
    _ALIAS_TO_KEY[_norm(_d.key)] = _d.key
    for _a in _d.aliases:
        _ALIAS_TO_KEY[_norm(_a)] = _d.key


def canonical_key(raw_name: str) -> str:
    """Map any raw parameter name onto a canonical key. Unknown names are returned
    trimmed but otherwise unchanged, so they still group with themselves."""
    if not raw_name:
        return raw_name
    return _ALIAS_TO_KEY.get(_norm(raw_name), raw_name.strip())


def label(key_or_name: str) -> str:
    """Korean display label for a canonical key. Falls back to the input (already a
    label, or an unknown parameter) unchanged."""
    if key_or_name in _KEY_TO_LABEL:
        return _KEY_TO_LABEL[key_or_name]
    return _KEY_TO_LABEL.get(canonical_key(key_or_name), key_or_name)


# ---- Equipment types ----
_EQUIPMENT_ALIASES: dict[str, str] = {
    "motor": "Motor", "전동기": "Motor", "모터": "Motor", "induction motor": "Motor",
    "pump": "Pump", "펌프": "Pump",
    "ahu": "AHU", "air handling unit": "AHU", "공조기": "AHU", "공기조화기": "AHU",
    "fan": "Fan", "송풍기": "Fan", "블로워": "Fan", "blower": "Fan",
    "compressor": "Compressor", "압축기": "Compressor",
    "transformer": "Transformer", "변압기": "Transformer", "tr": "Transformer",
    "valve": "Valve", "밸브": "Valve",
    "panel": "Panel", "배전반": "Panel", "분전반": "Panel", "mcc": "Panel", "switchgear": "Panel",
}


def canonical_equipment_type(raw_type: str) -> str:
    if not raw_type:
        return raw_type
    return _EQUIPMENT_ALIASES.get(raw_type.strip().lower(), raw_type.strip())


# ---- Units ----
# Same quantity, different spelling across documents — collapse to one canonical form so
# the deterministic comparison doesn't flag "m³/h vs m3/h" as a real discrepancy.
_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
_UNIT_ALIASES: dict[str, str] = {
    "mm²": "mm2", "㎟": "mm2", "sqmm": "mm2", "sq.mm": "mm2", "sqmm.": "mm2", "sq mm": "mm2",
    "m²": "m2", "㎡": "m2",
    "m³": "m3", "㎥": "m3",
    "m³/h": "m3/h", "㎥/h": "m3/h", "m3/hr": "m3/h", "m³/hr": "m3/h", "cmh": "m3/h", "nm3/h": "m3/h",
    "l/min": "L/min", "lpm": "L/min",
    "℃": "C", "°c": "C", "degc": "C", "deg.c": "C",
    "kw": "kW", "mw": "MW", "hp": "HP",
    "kv": "kV", "v": "V",
    "ma": "mA", "a": "A",
    "㎪": "kPa", "mpa": "MPa", "kpa": "kPa", "bar": "bar", "barg": "bar",
    "%": "%", "rpm": "rpm", "hz": "Hz",
}


def normalize_unit(unit: str | None) -> str | None:
    """Canonicalise a unit string: strip whitespace, fold Unicode superscripts (m³ → m3),
    and map common spellings (SQMM → mm2, ℃ → C). Unknown units pass through trimmed."""
    if not unit:
        return unit
    u = unit.strip().translate(_SUPERSCRIPT)
    return _UNIT_ALIASES.get(u.lower(), u)


# Cable cross-section often arrives as "4C x 25 SQMM", "3C+E 1x35mm²", "25SQ" etc.
# Pull out just the cross-section number so it compares as a value, not free text.
_CABLE_CSA_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*mm|sqmm|sq|mm2|mm²|㎟)\b", re.IGNORECASE
)


def clean_cable_value(raw_value: str) -> tuple[str, str | None]:
    """('4C x 25 SQMM') -> ('25', 'mm2'). Returns (value, unit); unit is None if we
    couldn't confidently parse a cross-section (value returned unchanged)."""
    if not raw_value:
        return raw_value, None
    m = _CABLE_CSA_RE.search(raw_value)
    if m:
        return m.group(1), "mm2"
    return raw_value, None
