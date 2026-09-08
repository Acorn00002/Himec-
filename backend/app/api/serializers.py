from app.db import models
from app.schemas.schemas import IssueOut
from app.services.parameters import label as parameter_label


def issue_to_out(issue: models.Issue) -> IssueOut:
    return IssueOut.model_validate({
        "id": issue.id,
        "project_id": issue.project_id,
        "equipment_id": issue.equipment_id,
        "equipment_tag": issue.equipment.tag if issue.equipment else None,
        "parameter_name": issue.parameter_name,
        "parameter_label": parameter_label(issue.parameter_name) if issue.parameter_name else None,
        "issue_type": issue.issue_type,
        "severity": issue.severity,
        "title": issue.title,
        "description": issue.description,
        "reasoning": issue.reasoning,
        "evidence": issue.evidence,
        "impact_items": issue.impact_items,
        "status": issue.status,
        "disposition": issue.disposition or "open",
        "review_comment": issue.review_comment,
        "reviewed_by": issue.reviewed_by,
        "reviewed_at": issue.reviewed_at,
        "created_at": issue.created_at,
    })
