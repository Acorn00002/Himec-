"""GEMINI_API_KEY missing/invalid, or the Gemini call itself failing, must never break
the app — upload/parsing/crosscheck stay usable via the deterministic path, just without
AI-extracted parameters for that document. Runs regardless of whether a real key is
configured in this environment (unlike test_ai_pipeline.py, which needs a real key)."""

from fastapi.testclient import TestClient

from app.db import models
from app.main import app
from app.services import extraction_pipeline
from app.services.ai import issue_reasoning, report_summary
from app.services.ai.llm_client import llm_client
from app.services.crosscheck_basic import ParameterComparison, SourceValue

client = TestClient(app)


def test_upload_succeeds_and_stays_parsed_when_no_api_key(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_client, "_api_key", "")
    assert not llm_client.is_configured

    project_id = client.post("/api/projects", json={"name": "No Key Test"}).json()["id"]
    txt_path = tmp_path / "spec.txt"
    txt_path.write_text("TAG: M-901\nPower: 15 kW\nVoltage: 380 V\n", encoding="utf-8")

    with open(txt_path, "rb") as f:
        resp = client.post(
            f"/api/projects/{project_id}/documents",
            files={"file": ("spec.txt", f, "text/plain")},
            data={"category": "spec"},
        )
    assert resp.status_code == 200, resp.text
    doc = resp.json()
    # deterministic parsing still ran (txt parser needs no AI), extraction just didn't
    assert doc["status"] == "parsed"

    # no equipment/parameters were created — nothing to extract them, and that's fine
    equipment = client.get(f"/api/projects/{project_id}/equipment").json()
    assert equipment == []


def test_extract_and_store_returns_false_without_crashing(monkeypatch):
    monkeypatch.setattr(llm_client, "_api_key", "")
    db = None
    try:
        from app.db.database import SessionLocal
        db = SessionLocal()
        project = models.Project(name="Fallback Unit Test", is_demo=False)
        db.add(project)
        db.flush()
        document = models.Document(
            project_id=project.id, filename="x.txt", doc_type="txt",
            category="spec", status="parsed",
        )
        db.add(document)
        db.flush()
        db.add(models.ExtractedChunk(
            document_id=document.id, location="전체", content_type="text", text="Power: 15 kW",
        ))
        db.flush()
        db.refresh(document)

        ran = extraction_pipeline.extract_and_store(db, project.id, document)
        assert ran is False
    finally:
        if db:
            db.close()


def test_issue_reasoning_falls_back_to_template_without_api_key(monkeypatch):
    monkeypatch.setattr(llm_client, "_api_key", "")
    comparison = ParameterComparison(
        name="정격출력",
        key="Power",
        sources=[
            SourceValue(document_id=1, document_name="사양서.pdf", value="15", unit="kW"),
            SourceValue(document_id=2, document_name="도면.pdf", value="18.5", unit="kW"),
        ],
        status="mismatch",
        reason="문서 간 값 편차가 허용 오차를 초과합니다.",
        kind="deviation_mismatch",
        deviation=0.2,
    )
    text = issue_reasoning.generate_reasoning("M-101", comparison, "HIGH", ["케이블 굵기 산정"])
    assert text  # non-empty fallback prose, no exception, no network call
    assert "정격출력" in text


def test_executive_summary_falls_back_without_api_key(monkeypatch):
    monkeypatch.setattr(llm_client, "_api_key", "")
    stats = {
        "document_count": 4, "equipment_count": 3, "issue_count": 5,
        "high_risk_count": 3, "medium_count": 1, "low_count": 1, "info_count": 0,
    }
    text = report_summary.generate_executive_summary("테스트 프로젝트", stats, ["정격출력 불일치"])
    assert text
    assert "5" in text  # issue_count shows up in the deterministic template
