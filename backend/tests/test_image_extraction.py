import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from app.core.config import GEMINI_API_KEY
from app.main import app

client = TestClient(app)

pytestmark = pytest.mark.skipif(not GEMINI_API_KEY, reason="GEMINI_API_KEY not configured")


def _make_nameplate_image(path):
    img = Image.new("RGB", (500, 300), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font = ImageFont.load_default(size=24)

    lines = [
        "MOTOR NAMEPLATE",
        "TAG: M-701",
        "MFR: LS Electric",
        "OUTPUT: 18.5 kW",
        "VOLTAGE: 380 V",
        "RPM: 1760",
    ]
    y = 15
    for line in lines:
        draw.text((20, y), line, fill="black", font=font)
        y += 40
    img.save(path)


def test_nameplate_image_extraction():
    project_resp = client.post("/api/projects", json={"name": "Image Extraction Test"})
    project_id = project_resp.json()["id"]

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "nameplate.png"
        _make_nameplate_image(img_path)

        with open(img_path, "rb") as f:
            resp = client.post(
                f"/api/projects/{project_id}/documents",
                files={"file": ("nameplate.png", f, "image/png")},
                data={"category": "drawing"},
            )
    assert resp.status_code == 200, resp.text
    doc = resp.json()
    assert doc["doc_type"] == "image"
    assert doc["status"] == "analyzed", "Gemini vision extraction should mark the image analyzed"

    equipment = client.get(f"/api/projects/{project_id}/equipment").json()
    tags = {e["tag"] for e in equipment}
    assert "M-701" in tags, f"expected M-701 to be extracted from the nameplate image, got tags={tags}"

    detail = client.get(f"/api/projects/{project_id}/equipment/M-701").json()
    param_keys = {p["key"] for p in detail["parameters"]}
    assert "Power" in param_keys
    power_row = next(p for p in detail["parameters"] if p["key"] == "Power")
    assert power_row["sources"][0]["value"] == "18.5"
