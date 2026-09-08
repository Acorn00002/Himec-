import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.serializers import issue_to_out
from app.db import models
from app.db.database import get_db
from app.schemas.schemas import DISPOSITION_VALUES, IssueOut, IssueReviewIn

router = APIRouter(tags=["issues"])

SEVERITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}

# How a disposition maps onto the coarse `status` used by the dashboard's review-progress
# gauge. "open" keeps the issue in the un-reviewed bucket; anything else counts as reviewed.
DISPOSITION_TO_STATUS = {
    "open": "open",
    "intentional": "reviewed",
    "action_required": "reviewed",
    "resolved": "resolved",
}


@router.get("/api/projects/{project_id}/issues", response_model=list[IssueOut])
def list_issues(project_id: int, severity: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Issue).filter(models.Issue.project_id == project_id)
    if severity:
        query = query.filter(models.Issue.severity == severity.upper())
    issues = query.all()
    issues.sort(key=lambda i: SEVERITY_RANK.get(i.severity, -1), reverse=True)
    return [issue_to_out(i) for i in issues]


@router.get("/api/issues/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.get(models.Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue_to_out(issue)


@router.patch("/api/issues/{issue_id}/review", response_model=IssueOut)
def update_issue_review(issue_id: int, payload: IssueReviewIn, db: Session = Depends(get_db)):
    """Record the reviewing engineer's decision on an issue: whether the discrepancy is an
    intentional design difference or needs action, plus a free-text review note / exception
    reason. This is the Human-in-the-Loop layer — it never changes the AI's findings, only
    annotates them, and the annotations flow through to the exported PDF report."""
    issue = db.get(models.Issue, issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    if payload.disposition is not None:
        if payload.disposition not in DISPOSITION_VALUES:
            raise HTTPException(
                status_code=422,
                detail=f"disposition must be one of {', '.join(DISPOSITION_VALUES)}",
            )
        issue.disposition = payload.disposition
        issue.status = DISPOSITION_TO_STATUS[payload.disposition]

    if payload.review_comment is not None:
        issue.review_comment = payload.review_comment.strip() or None

    if payload.reviewed_by is not None:
        issue.reviewed_by = payload.reviewed_by.strip() or None

    # Stamp the review time whenever there is any review content, clear it once the issue
    # is fully reset to an un-reviewed, un-commented state.
    if issue.disposition != "open" or issue.review_comment:
        issue.reviewed_at = dt.datetime.utcnow()
    else:
        issue.reviewed_at = None

    db.commit()
    db.refresh(issue)
    return issue_to_out(issue)
