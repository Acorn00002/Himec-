from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.schemas import DemoLoadOut
from app.services.demo_data import seed_demo_project

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/load", response_model=DemoLoadOut)
def load_demo_project(db: Session = Depends(get_db)):
    project = seed_demo_project(db)
    return DemoLoadOut(
        project_id=project.id,
        message="데모 프로젝트를 로드했습니다. 5개 설비, 5개 문서에서 의도적으로 주입된 불일치를 확인할 수 있습니다.",
    )
