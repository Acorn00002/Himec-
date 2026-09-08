from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.schemas import DashboardOut

router = APIRouter(prefix="/api/projects", tags=["dashboard"])

SEVERITY_ORDER = ["HIGH", "MEDIUM", "LOW", "INFO"]


@router.get("/{project_id}/dashboard", response_model=DashboardOut)
def get_dashboard(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    document_count = db.query(func.count(models.Document.id)).filter(
        models.Document.project_id == project_id
    ).scalar()
    equipment_count = db.query(func.count(models.Equipment.id)).filter(
        models.Equipment.project_id == project_id
    ).scalar()

    issues = db.query(models.Issue).filter(models.Issue.project_id == project_id).all()
    counts = {s: 0 for s in SEVERITY_ORDER}
    for issue in issues:
        if issue.severity in counts:
            counts[issue.severity] += 1

    issue_count = len(issues)
    reviewed = sum(1 for i in issues if i.status != "open")
    progress = int(round((reviewed / issue_count) * 100)) if issue_count else 100

    return DashboardOut(
        project_id=project.id,
        project_name=project.name,
        mode="demo" if project.is_demo else "live",
        document_count=document_count,
        equipment_count=equipment_count,
        issue_count=issue_count,
        high_risk_count=counts["HIGH"],
        medium_count=counts["MEDIUM"],
        low_count=counts["LOW"],
        info_count=counts["INFO"],
        reviewed_count=reviewed,
        open_count=issue_count - reviewed,
        review_progress_percent=progress,
        severity_breakdown=[{"severity": s, "count": counts[s]} for s in SEVERITY_ORDER],
    )
