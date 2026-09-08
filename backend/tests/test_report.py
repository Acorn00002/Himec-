from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_report_pdf_for_demo_project():
    resp = client.post("/api/demo/load")
    project_id = resp.json()["project_id"]

    report_resp = client.get(f"/api/projects/{project_id}/report.pdf")
    assert report_resp.status_code == 200
    assert report_resp.headers["content-type"] == "application/pdf"
    assert report_resp.content.startswith(b"%PDF")
    assert len(report_resp.content) > 1000
