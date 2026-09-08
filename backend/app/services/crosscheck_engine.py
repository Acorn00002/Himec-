"""Phase 10~11 — turns ParameterValue mismatches (+ calc/missing checks) into Issues
with severity, evidence, and impact analysis for a real (non-demo) project.

Orchestration only: numeric comparison is services/crosscheck_basic, engineering
calculation checks are services/engineering_rules, severity/impact/required-parameter
policy is services/issue_rules (all deterministic), and only the reasoning prose is
asked of Gemini (services/ai/issue_reasoning), with a non-AI fallback. This mirrors
how services/demo_data.py hand-curates the same fields for the demo project, so both
code paths produce Issues with the same shape.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from app.db import models
from app.services.ai.issue_reasoning import generate_reasoning
from app.services.crosscheck_basic import ParameterComparison, build_parameter_rows
from app.services.engineering_rules import CalcFinding, run_calc_checks
from app.services.issue_rules import (
    REQUIRED_PARAMS_BY_TYPE,
    decide_severity,
    impact_items_for,
    issue_type_for,
    missing_severity,
)
from app.services.parameters import canonical_key, label as parameter_label


def _title_for(comparison: ParameterComparison) -> str:
    if comparison.kind == "dimension_mismatch":
        return f"{comparison.name} 값의 단위 체계가 문서마다 다릅니다"
    if comparison.kind == "text_mismatch":
        return f"{comparison.name} 값이 문서마다 다릅니다"
    return f"{comparison.name} 값이 문서별로 상이합니다"


def _description_for(tag: str, comparison: ParameterComparison) -> str:
    parts = [
        f"{s.document_name}: {s.value}{(' ' + s.unit) if s.unit else ''}" for s in comparison.sources
    ]
    return f"TAG {tag}의 {comparison.name} 값이 문서마다 다르게 기재되어 있습니다 ({' / '.join(parts)})."


def _mismatch_issues(project: models.Project, eq: models.Equipment, parameter_values: list) -> list[models.Issue]:
    issues = []
    for comparison in build_parameter_rows(parameter_values):
        if comparison.status != "mismatch":
            continue

        severity = decide_severity(comparison.key, comparison.kind, comparison.deviation)
        impact_items = impact_items_for(comparison.key)
        issue_type = issue_type_for(comparison.kind)
        reasoning = generate_reasoning(eq.tag, comparison, severity, impact_items)

        issues.append(models.Issue(
            project_id=project.id,
            equipment_id=eq.id,
            parameter_name=comparison.key,
            issue_type=issue_type,
            severity=severity,
            title=_title_for(comparison),
            description=_description_for(eq.tag, comparison),
            reasoning=reasoning,
            evidence=[
                {"document": s.document_name, "document_id": s.document_id, "location": s.location,
                 "value": s.value, "unit": s.unit, "raw_snippet": s.raw_snippet}
                for s in comparison.sources
            ],
            impact_items=impact_items,
            status="open",
        ))
    return issues


def _calc_issue(project: models.Project, eq: models.Equipment, finding: CalcFinding) -> models.Issue:
    return models.Issue(
        project_id=project.id,
        equipment_id=eq.id,
        parameter_name=None,
        issue_type="calc_mismatch",
        severity=finding.severity,
        title=finding.title,
        description=finding.message,
        reasoning=(
            f"이 판단은 문서 간 비교가 아니라 표준 전기공학 계산식에 따른 검증입니다 "
            f"(계산값 {finding.calculated_value}{finding.unit} vs 기재값 {finding.reported_value}{finding.unit})."
        ),
        evidence=[
            {"document": pv.document.filename, "document_id": pv.document_id, "location": pv.location,
             "value": pv.value, "unit": pv.unit, "raw_snippet": pv.raw_snippet}
            for pv in finding.inputs
        ],
        impact_items=finding.impact_items,
        status="open",
    )


def _missing_issues(project: models.Project, eq: models.Equipment, parameter_values: list) -> list[models.Issue]:
    required = REQUIRED_PARAMS_BY_TYPE.get(eq.equipment_type)
    if not required or not parameter_values:
        return []

    present_names = {canonical_key(pv.name) for pv in parameter_values}
    documents = {pv.document_id: pv.document for pv in parameter_values}.values()

    issues = []
    for name in required:
        if name in present_names:
            continue
        severity = missing_severity(name)
        label = parameter_label(name)
        issues.append(models.Issue(
            project_id=project.id,
            equipment_id=eq.id,
            parameter_name=name,
            issue_type="missing",
            severity=severity,
            title=f"{label} 값이 누락되었습니다",
            description=(
                f"TAG {eq.tag}({eq.equipment_type})에 대해 업로드된 {len(documents)}개 문서 어디에도 "
                f"{label} 값이 없습니다."
            ),
            reasoning=(
                f"{eq.equipment_type} 유형 설비는 일반적으로 {label} 정보가 필요하지만 "
                f"현재 업로드된 문서에서는 확인되지 않았습니다. 설계 검토 시 누락 여부를 확인해야 합니다."
            ),
            evidence=[
                {"document": doc.filename, "document_id": doc.id, "location": None,
                 "value": "(not found)", "unit": None, "raw_snippet": None}
                for doc in documents
            ],
            impact_items=impact_items_for(name),
            status="open",
        ))
    return issues


def _review_fingerprint(issue: models.Issue) -> tuple:
    """Stable identity of an issue across re-runs — an engineer's review note should
    survive re-running the cross-check after a document is re-uploaded."""
    return (issue.equipment_id, issue.parameter_name or "", issue.issue_type)


def run_crosscheck_for_project(db: Session, project: models.Project) -> list[models.Issue]:
    prior_issues = db.query(models.Issue).filter(models.Issue.project_id == project.id).all()
    prior_review = {
        _review_fingerprint(i): {
            "status": i.status,
            "disposition": i.disposition or "open",
            "review_comment": i.review_comment,
            "reviewed_by": i.reviewed_by,
            "reviewed_at": i.reviewed_at,
        }
        for i in prior_issues
        if (i.disposition and i.disposition != "open") or i.review_comment
    }

    db.query(models.Issue).filter(models.Issue.project_id == project.id).delete()
    db.flush()

    equipment_list = db.query(models.Equipment).filter(models.Equipment.project_id == project.id).all()

    created: list[models.Issue] = []
    for eq in equipment_list:
        parameter_values = db.query(models.ParameterValue).options(
            joinedload(models.ParameterValue.document)
        ).filter(models.ParameterValue.equipment_id == eq.id).all()

        created.extend(_mismatch_issues(project, eq, parameter_values))
        for finding in run_calc_checks(parameter_values):
            created.append(_calc_issue(project, eq, finding))
        created.extend(_missing_issues(project, eq, parameter_values))

    for issue in created:
        carried = prior_review.get(_review_fingerprint(issue))
        if carried:
            issue.status = carried["status"]
            issue.disposition = carried["disposition"]
            issue.review_comment = carried["review_comment"]
            issue.reviewed_by = carried["reviewed_by"]
            issue.reviewed_at = carried["reviewed_at"]

    db.add_all(created)
    db.commit()
    for issue in created:
        db.refresh(issue)
    return created
