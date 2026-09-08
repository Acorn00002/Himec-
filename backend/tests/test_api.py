from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_demo_flow():
    resp = client.post("/api/demo/load")
    assert resp.status_code == 200
    project_id = resp.json()["project_id"]

    dashboard = client.get(f"/api/projects/{project_id}/dashboard").json()
    assert dashboard["equipment_count"] == 5
    assert dashboard["document_count"] == 5
    assert dashboard["issue_count"] >= 5
    assert dashboard["high_risk_count"] >= 2

    equipment_list = client.get(f"/api/projects/{project_id}/equipment").json()
    tags = {e["tag"] for e in equipment_list}
    assert tags == {"M-101", "M-102", "P-101", "P-102", "AHU-101"}

    m101 = client.get(f"/api/projects/{project_id}/equipment/M-101").json()
    power_row = next(p for p in m101["parameters"] if p["key"] == "Power")
    assert power_row["name"] == "정격출력"  # UI shows the Korean label
    assert power_row["status"] == "mismatch"
    assert len(power_row["sources"]) == 4

    voltage_row = next(p for p in m101["parameters"] if p["key"] == "Voltage")
    assert voltage_row["status"] == "match"

    issues = client.get(f"/api/projects/{project_id}/issues").json()
    assert len(issues) >= 5
    assert issues[0]["severity"] == "HIGH"  # sorted by severity desc

    issue_detail = client.get(f"/api/issues/{issues[0]['id']}").json()
    assert issue_detail["evidence"]
    assert issue_detail["impact_items"]


def test_issue_review_disposition_and_comment_flow():
    project_id = client.post("/api/demo/load").json()["project_id"]
    issues = client.get(f"/api/projects/{project_id}/issues").json()

    # every issue carries the new review fields, defaulting to un-reviewed
    open_issue = next(i for i in issues if i["disposition"] == "open")
    assert open_issue["review_comment"] is None
    assert open_issue["reviewed_at"] is None

    # evidence rows now carry the original snippet for traceability
    assert any(e.get("raw_snippet") for e in open_issue["evidence"])

    resp = client.patch(
        f"/api/issues/{open_issue['id']}/review",
        json={
            "disposition": "intentional",
            "review_comment": "  설계 마진으로 의도된 차이  ",
            "reviewed_by": "테스트 엔지니어",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["disposition"] == "intentional"
    assert body["status"] == "reviewed"  # counts toward dashboard review progress
    assert body["review_comment"] == "설계 마진으로 의도된 차이"  # trimmed
    assert body["reviewed_at"] is not None

    # curated demo issues can already come pre-reviewed
    assert any(i["disposition"] == "action_required" and i["review_comment"] for i in issues)

    # invalid disposition rejected
    bad = client.patch(f"/api/issues/{open_issue['id']}/review", json={"disposition": "nope"})
    assert bad.status_code == 422


def test_issue_review_survives_crosscheck_rerun(tmp_path):
    project_id = client.post("/api/projects", json={"name": "Rerun Project"}).json()["id"]

    for name in ("spec.txt", "drawing.txt"):
        f = tmp_path / name
        f.write_text(
            "TAG: M-201\nEquipment Type: Motor\n"
            f"Power: {'15' if name == 'spec.txt' else '22'} kW\nVoltage: 380 V\n"
        )
        with open(f, "rb") as fh:
            client.post(
                f"/api/projects/{project_id}/documents",
                files={"file": (name, fh, "text/plain")},
                data={"category": "spec"},
            )

    client.post(f"/api/projects/{project_id}/crosscheck/run")
    issues = client.get(f"/api/projects/{project_id}/issues").json()
    if not issues:
        return  # extraction needs the AI layer; nothing to assert without it

    target = issues[0]
    client.patch(
        f"/api/issues/{target['id']}/review",
        json={"disposition": "action_required", "review_comment": "도면 재발행 요청함"},
    )

    client.post(f"/api/projects/{project_id}/crosscheck/run")
    after = client.get(f"/api/projects/{project_id}/issues").json()
    carried = [i for i in after if i["review_comment"] == "도면 재발행 요청함"]
    assert carried and carried[0]["disposition"] == "action_required"


def test_create_project_and_upload_document(tmp_path):
    resp = client.post("/api/projects", json={"name": "Test Project"})
    assert resp.status_code == 200
    project_id = resp.json()["id"]

    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("hello")

    with open(sample_file, "rb") as f:
        resp = client.post(
            f"/api/projects/{project_id}/documents",
            files={"file": ("sample.txt", f, "text/plain")},
            data={"category": "spec"},
        )
    assert resp.status_code == 200
    assert resp.json()["doc_type"] == "txt"

    docs = client.get(f"/api/projects/{project_id}/documents").json()
    assert len(docs) == 1
