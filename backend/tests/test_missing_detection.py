from app.db import models
from app.db.database import SessionLocal
from app.main import app  # noqa: F401  (ensures tables are created via create_all)
from app.services.crosscheck_engine import run_crosscheck_for_project


def test_missing_required_parameter_is_flagged():
    db = SessionLocal()
    try:
        project = models.Project(name="Missing Param Test", is_demo=False)
        db.add(project)
        db.flush()

        document = models.Document(
            project_id=project.id, filename="Spec.pdf", doc_type="pdf",
            category="spec", status="analyzed",
        )
        db.add(document)
        db.flush()

        equipment = models.Equipment(project_id=project.id, tag="M-901", equipment_type="Motor")
        db.add(equipment)
        db.flush()

        # Motor requires Power, Voltage, RPM, Efficiency — Efficiency is deliberately absent.
        for name, value, unit in [("Power", "10", "kW"), ("Voltage", "380", "V"), ("RPM", "1450", None)]:
            db.add(models.ParameterValue(
                equipment_id=equipment.id, document_id=document.id,
                name=name, value=value, numeric_value=float(value), unit=unit,
            ))
        db.commit()

        issues = run_crosscheck_for_project(db, project)
        missing = [i for i in issues if i.issue_type == "missing"]
        assert len(missing) == 1
        assert missing[0].parameter_name == "Efficiency"
        assert missing[0].severity == "LOW"
        assert missing[0].evidence[0]["document"] == "Spec.pdf"
        assert missing[0].evidence[0]["document_id"] == document.id
    finally:
        db.close()


def test_unrecognized_equipment_type_skips_missing_check():
    db = SessionLocal()
    try:
        project = models.Project(name="Unknown Type Test", is_demo=False)
        db.add(project)
        db.flush()
        document = models.Document(
            project_id=project.id, filename="Spec.pdf", doc_type="pdf", category="spec", status="analyzed",
        )
        db.add(document)
        db.flush()
        equipment = models.Equipment(project_id=project.id, tag="X-1", equipment_type="Valve")
        db.add(equipment)
        db.flush()
        db.add(models.ParameterValue(
            equipment_id=equipment.id, document_id=document.id, name="Power", value="1", numeric_value=1.0, unit="kW",
        ))
        db.commit()

        issues = run_crosscheck_for_project(db, project)
        assert [i for i in issues if i.issue_type == "missing"] == []
    finally:
        db.close()
