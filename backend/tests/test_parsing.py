import csv

import openpyxl
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import app

client = TestClient(app)


def _new_project() -> int:
    resp = client.post("/api/projects", json={"name": "Parsing Test Project"})
    assert resp.status_code == 200
    return resp.json()["id"]


def _upload(project_id: int, path, filename: str, content_type: str, category="spec"):
    with open(path, "rb") as f:
        resp = client.post(
            f"/api/projects/{project_id}/documents",
            files={"file": (filename, f, content_type)},
            data={"category": category},
        )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_pdf_parsing(tmp_path):
    pdf_path = tmp_path / "Motor_Spec.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=(300, 300))
    c.drawString(20, 200, "TAG: M-201")
    c.drawString(20, 180, "Power: 30 kW")
    c.drawString(20, 160, "Voltage: 400 V")
    c.showPage()
    c.save()

    project_id = _new_project()
    doc = _upload(project_id, pdf_path, "Motor_Spec.pdf", "application/pdf")
    assert doc["status"] in {"parsed", "analyzed"}  # "analyzed" if GEMINI_API_KEY happens to be configured

    chunks = client.get(f"/api/projects/{project_id}/documents/{doc['id']}/content").json()
    assert len(chunks) == 1
    assert chunks[0]["location"] == "p.1"
    assert "M-201" in chunks[0]["text"]
    assert "30 kW" in chunks[0]["text"]


def test_xlsx_parsing(tmp_path):
    xlsx_path = tmp_path / "Equipment_List.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["TAG", "Manufacturer", "Power"])
    ws.append(["M-201", "Siemens", 30])
    wb.save(xlsx_path)

    project_id = _new_project()
    doc = _upload(
        project_id, xlsx_path, "Equipment_List.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        category="equipment_list",
    )
    assert doc["status"] in {"parsed", "analyzed"}  # "analyzed" if GEMINI_API_KEY happens to be configured

    chunks = client.get(f"/api/projects/{project_id}/documents/{doc['id']}/content").json()
    assert len(chunks) == 1
    assert chunks[0]["location"] == "Sheet1"
    assert "Siemens" in chunks[0]["text"]
    assert "Row2" in chunks[0]["text"]


def test_csv_parsing(tmp_path):
    csv_path = tmp_path / "Load_Calculation.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["TAG", "Power"])
        writer.writerow(["M-201", "33"])

    project_id = _new_project()
    doc = _upload(project_id, csv_path, "Load_Calculation.csv", "text/csv", category="calculation")
    assert doc["status"] in {"parsed", "analyzed"}  # "analyzed" if GEMINI_API_KEY happens to be configured

    chunks = client.get(f"/api/projects/{project_id}/documents/{doc['id']}/content").json()
    assert len(chunks) == 1
    assert "33" in chunks[0]["text"]


def test_txt_parsing(tmp_path):
    txt_path = tmp_path / "notes.txt"
    txt_path.write_text("TAG M-201 power rating is 30 kW.", encoding="utf-8")

    project_id = _new_project()
    doc = _upload(project_id, txt_path, "notes.txt", "text/plain")
    assert doc["status"] in {"parsed", "analyzed"}  # "analyzed" if GEMINI_API_KEY happens to be configured

    chunks = client.get(f"/api/projects/{project_id}/documents/{doc['id']}/content").json()
    assert len(chunks) == 1
    assert "30 kW" in chunks[0]["text"]


def test_image_upload_has_no_chunks_but_succeeds(tmp_path):
    img_path = tmp_path / "nameplate.png"
    # minimal 1x1 PNG
    img_path.write_bytes(bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c6360000002000100"
        "5e2707a30000000049454e44ae426082"
    ))

    project_id = _new_project()
    doc = _upload(project_id, img_path, "nameplate.png", "image/png", category="drawing")
    assert doc["status"] in {"uploaded", "analyzed"}  # no deterministic parser for images either way

    chunks = client.get(f"/api/projects/{project_id}/documents/{doc['id']}/content").json()
    assert chunks == []
