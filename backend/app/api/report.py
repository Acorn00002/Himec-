import re
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.services.report import generate_report_pdf

router = APIRouter(prefix="/api/projects", tags=["report"])


@router.get("/{project_id}/report.pdf")
def get_report_pdf(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    pdf_bytes = generate_report_pdf(db, project)

    # Content-Disposition headers must be latin-1; project names can contain Korean /
    # em dashes, so ship an ASCII fallback plus an RFC 5987 UTF-8 filename*.
    raw_name = f"{project.name}_CrossCheck_Report.pdf"
    ascii_fallback = re.sub(r"[^A-Za-z0-9._-]", "_", raw_name) or "CrossCheck_Report.pdf"
    utf8_name = urllib.parse.quote(raw_name)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{utf8_name}'
        },
    )
