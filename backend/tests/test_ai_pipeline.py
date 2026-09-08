import openpyxl
import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.core.config import GEMINI_API_KEY
from app.main import app

client = TestClient(app)

pytestmark = pytest.mark.skipif(not GEMINI_API_KEY, reason="GEMINI_API_KEY not configured")


def _new_project() -> int:
    resp = client.post("/api/projects", json={"name": "AI Pipeline Test"})
    assert resp.status_code == 200
    return resp.json()["id"]


def _upload(project_id: int, path, filename: str, content_type: str, category: str):
    with open(path, "rb") as f:
        resp = client.post(
            f"/api/projects/{project_id}/documents",
            files={"file": (filename, f, content_type)},
            data={"category": category},
        )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_extraction_and_crosscheck_end_to_end(tmp_path):
    project_id = _new_project()

    pdf_path = tmp_path / "Motor_Spec.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(300, 300))
    c.drawString(20, 200, "TAG: M-301")
    c.drawString(20, 180, "Power: 20 kW")
    c.drawString(20, 160, "Voltage: 400 V")
    c.showPage()
    c.save()
    doc1 = _upload(project_id, pdf_path, "Motor_Spec.pdf", "application/pdf", "spec")
    assert doc1["status"] == "analyzed", "Gemini extraction should mark the document analyzed"

    xlsx_path = tmp_path / "Load_Calculation.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["TAG", "Power"])
    ws.append(["M-301", "35 kW"])
    wb.save(xlsx_path)
    doc2 = _upload(
        project_id, xlsx_path, "Load_Calculation.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "calculation",
    )
    assert doc2["status"] == "analyzed"

    equipment = client.get(f"/api/projects/{project_id}/equipment").json()
    tags = {e["tag"] for e in equipment}
    assert "M-301" in tags

    detail = client.get(f"/api/projects/{project_id}/equipment/M-301").json()
    power_row = next((p for p in detail["parameters"] if p["key"] == "Power"), None)
    assert power_row is not None
    assert len(power_row["sources"]) == 2

    run_resp = client.post(f"/api/projects/{project_id}/crosscheck/run")
    assert run_resp.status_code == 200
    result = run_resp.json()
    assert result["issue_count"] >= 1

    issues = client.get(f"/api/projects/{project_id}/issues").json()
    power_issue = next((i for i in issues if i["parameter_name"] == "Power"), None)
    assert power_issue is not None
    assert power_issue["severity"] in {"HIGH", "MEDIUM"}
    assert power_issue["evidence"]
    assert power_issue["impact_items"]
    assert power_issue["reasoning"]


def test_crosscheck_refuses_demo_project():
    resp = client.post("/api/demo/load")
    project_id = resp.json()["project_id"]
    run_resp = client.post(f"/api/projects/{project_id}/crosscheck/run")
    assert run_resp.status_code == 400
