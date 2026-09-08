from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.services.crosscheck_engine import run_crosscheck_for_project

router = APIRouter(prefix="/api/projects", tags=["crosscheck"])


class CrossCheckRunOut(BaseModel):
    issue_count: int
    high_risk_count: int
    equipment_count: int


@router.post("/{project_id}/crosscheck/run", response_model=CrossCheckRunOut)
def run_crosscheck(project_id: int, db: Session = Depends(get_db)):
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.is_demo:
        raise HTTPException(
            status_code=400,
            detail="데모 프로젝트는 큐레이션된 데이터를 사용하므로 CrossCheck를 다시 실행할 수 없습니다.",
        )

    issues = run_crosscheck_for_project(db, project)
    equipment_count = db.query(models.Equipment).filter(models.Equipment.project_id == project_id).count()
    high_risk_count = sum(1 for i in issues if i.severity == "HIGH")

    return CrossCheckRunOut(
        issue_count=len(issues),
        high_risk_count=high_risk_count,
        equipment_count=equipment_count,
    )
