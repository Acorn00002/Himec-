from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.serializers import issue_to_out
from app.db import models
from app.db.database import get_db
from app.schemas.schemas import EquipmentDetail, EquipmentSummary, ParameterRow, ParameterSourceValue
from app.services.crosscheck_basic import build_parameter_rows
from app.services.parameters import label as parameter_label

router = APIRouter(prefix="/api/projects", tags=["equipment"])

SEVERITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}

_ISSUE_TYPE_SUFFIX = {
    "value_mismatch": "불일치",
    "spec_mismatch": "불일치",
    "unit_mismatch": "단위 불일치",
    "missing": "누락",
    "abnormal_value": "이상값",
    "calc_mismatch": "계산값 불일치",
}


def _short_issue_label(issue: models.Issue) -> str:
    base = parameter_label(issue.parameter_name) if issue.parameter_name else None
    if base:
        return f"{base} {_ISSUE_TYPE_SUFFIX.get(issue.issue_type, '이슈')}"
    return issue.title


@router.get("/{project_id}/equipment", response_model=list[EquipmentSummary])
def list_equipment(project_id: int, db: Session = Depends(get_db)):
    equipment_list = db.query(models.Equipment).filter(models.Equipment.project_id == project_id).all()

    result = []
    for eq in equipment_list:
        doc_count = db.query(func.count(func.distinct(models.ParameterValue.document_id))).filter(
            models.ParameterValue.equipment_id == eq.id
        ).scalar()
        issues = db.query(models.Issue).filter(models.Issue.equipment_id == eq.id).all()
        max_severity = None
        top_issue_label = None
        if issues:
            top_issue = max(issues, key=lambda i: SEVERITY_RANK.get(i.severity, -1))
            max_severity = top_issue.severity
            top_issue_label = _short_issue_label(top_issue)
        result.append(EquipmentSummary(
            id=eq.id,
            tag=eq.tag,
            equipment_type=eq.equipment_type,
            document_count=doc_count or 0,
            issue_count=len(issues),
            max_severity=max_severity,
            top_issue_label=top_issue_label,
        ))
    return result


@router.get("/{project_id}/equipment/{tag}", response_model=EquipmentDetail)
def get_equipment_detail(project_id: int, tag: str, db: Session = Depends(get_db)):
    eq = db.query(models.Equipment).filter(
        models.Equipment.project_id == project_id, models.Equipment.tag == tag
    ).first()
    if eq is None:
        raise HTTPException(status_code=404, detail="Equipment not found")

    parameter_values = db.query(models.ParameterValue).options(
        joinedload(models.ParameterValue.document)
    ).filter(models.ParameterValue.equipment_id == eq.id).all()

    comparisons = build_parameter_rows(parameter_values)
    parameters = [
        ParameterRow(
            name=c.name,
            key=c.key,
            status=c.status,
            sources=[
                ParameterSourceValue(
                    document_id=s.document_id,
                    document_name=s.document_name,
                    value=s.value,
                    unit=s.unit,
                    location=s.location,
                    raw_snippet=s.raw_snippet,
                )
                for s in c.sources
            ],
        )
        for c in comparisons
    ]

    issues = db.query(models.Issue).filter(models.Issue.equipment_id == eq.id).all()

    return EquipmentDetail(
        id=eq.id,
        tag=eq.tag,
        equipment_type=eq.equipment_type,
        parameters=parameters,
        issues=[issue_to_out(i) for i in issues],
    )
