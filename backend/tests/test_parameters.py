"""Cross-language parameter/equipment-type normalization — the thing that lets a
Korean spec sheet and an English drawing be compared against each other."""

from app.db import models
from app.db.database import SessionLocal
from app.main import app  # noqa: F401  (ensures tables exist)
from app.services.crosscheck_basic import build_parameter_rows
from app.services.crosscheck_engine import run_crosscheck_for_project
from app.services.parameters import (
    canonical_equipment_type,
    canonical_key,
    clean_cable_value,
    label,
    normalize_unit,
)


def test_canonical_key_maps_korean_and_english_aliases():
    for raw in ("Power", "정격출력", "출력", "Rated Output", "kW", "정격 출력(kW)"):
        assert canonical_key(raw) == "Power", raw
    assert canonical_key("정격전압") == "Voltage"
    assert canonical_key("MCCB") == "Breaker Size"
    assert canonical_key("제작사") == "Manufacturer"
    # unknown names pass through untouched so they still group with themselves
    assert canonical_key("Rotor Bar Count") == "Rotor Bar Count"


def test_label_is_korean_for_known_keys():
    assert label("Power") == "정격출력"
    assert label("정격출력") == "정격출력"
    assert label("Unmapped") == "Unmapped"


def test_unit_normalization_folds_unicode_and_synonyms():
    # the m³/h (superscript) vs m3/h case that caused false "unit mismatch" flags
    assert normalize_unit("m³/h") == "m3/h"
    assert normalize_unit("m3/h") == "m3/h"
    assert normalize_unit("SQMM") == "mm2"
    assert normalize_unit("mm²") == "mm2"
    assert normalize_unit("℃") == "C"
    assert normalize_unit(None) is None
    assert normalize_unit("kW") == "kW"


def test_cable_value_cleanup_extracts_cross_section():
    assert clean_cable_value("4C x 25 SQMM") == ("25", "mm2")
    assert clean_cable_value("3C+E 1x35mm²") == ("35", "mm2")
    assert clean_cable_value("25mm2") == ("25", "mm2")
    # not a cable spec -> left as-is
    assert clean_cable_value("TBD")[1] is None


def test_flow_with_unicode_unit_still_matches():
    ko = models.Document(id=1, project_id=1, filename="사양서.pdf", doc_type="pdf", category="spec", status="analyzed")
    xls = models.Document(id=2, project_id=1, filename="목록.xlsx", doc_type="xlsx", category="equipment_list", status="analyzed")
    rows = build_parameter_rows([
        _pv("Flow", 120, "m³/h", ko),
        _pv("Flow", 120, "m3/h", xls),
    ])
    assert rows[0].key == "Flow"
    assert rows[0].status == "match"  # was "mismatch" before unit normalization


def test_equipment_type_normalization():
    assert canonical_equipment_type("전동기") == "Motor"
    assert canonical_equipment_type("PUMP") == "Pump"
    assert canonical_equipment_type("변압기") == "Transformer"
    assert canonical_equipment_type("Chiller") == "Chiller"


def _pv(name, value, unit, doc):
    pv = models.ParameterValue(
        equipment_id=1, document_id=doc.id, name=name, value=str(value),
        numeric_value=float(value) if str(value).replace(".", "").isdigit() else None, unit=unit,
    )
    pv.document = doc
    return pv


def test_korean_and_english_values_collapse_into_one_comparison_row():
    ko = models.Document(id=1, project_id=1, filename="사양서.pdf", doc_type="pdf", category="spec", status="analyzed")
    en = models.Document(id=2, project_id=1, filename="drawing.pdf", doc_type="pdf", category="drawing", status="analyzed")

    rows = build_parameter_rows([
        _pv("정격출력", 7.5, "kW", ko),
        _pv("Rated Output", 11, "kW", en),
        _pv("정격전압", 380, "V", ko),
        _pv("Voltage", 380, "V", en),
    ])

    by_key = {r.key: r for r in rows}
    assert set(by_key) == {"Power", "Voltage"}
    assert by_key["Power"].name == "정격출력"
    assert len(by_key["Power"].sources) == 2
    assert by_key["Power"].status == "mismatch"
    assert by_key["Voltage"].status == "match"


def test_missing_detection_uses_canonical_names():
    db = SessionLocal()
    try:
        project = models.Project(name="KO Missing Test", is_demo=False)
        db.add(project)
        db.flush()
        doc = models.Document(
            project_id=project.id, filename="펌프사양.pdf", doc_type="pdf", category="spec", status="analyzed",
        )
        db.add(doc)
        db.flush()
        eq = models.Equipment(project_id=project.id, tag="P-901", equipment_type="Pump")
        db.add(eq)
        db.flush()
        # Pump requires Flow, Pressure, Power — supply Korean-named Flow + Power, omit Pressure.
        for name, val, unit in [("유량", "45", "m3/h"), ("정격출력", "7.5", "kW")]:
            db.add(models.ParameterValue(
                equipment_id=eq.id, document_id=doc.id, name=name, value=val,
                numeric_value=float(val), unit=unit,
            ))
        db.commit()

        issues = run_crosscheck_for_project(db, project)
        missing = [i for i in issues if i.issue_type == "missing"]
        # Flow + Power are present (via aliases) so only Pressure should be flagged.
        assert [i.parameter_name for i in missing] == ["Pressure"]
    finally:
        db.close()
