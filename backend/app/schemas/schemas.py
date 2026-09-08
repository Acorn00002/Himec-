import datetime as dt

from pydantic import BaseModel, ConfigDict, computed_field


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_demo: bool
    created_at: dt.datetime

    @computed_field
    @property
    def mode(self) -> str:
        """'demo' = 미리 준비된 샘플 데이터, 'live' = 업로드 문서 기반 분석.
        UI가 이 값으로 데이터 출처를 명확히 구분한다 (실제 분석인 것처럼 표시 금지)."""
        return "demo" if self.is_demo else "live"


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    filename: str
    doc_type: str
    category: str
    status: str
    uploaded_at: dt.datetime


class ExtractedChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    location: str
    content_type: str
    text: str


class ParameterSourceValue(BaseModel):
    """One document's reported value for a parameter — used inside the cross-check matrix."""

    document_id: int
    document_name: str
    value: str
    unit: str | None = None
    location: str | None = None
    raw_snippet: str | None = None


class ParameterRow(BaseModel):
    """One row of the CrossCheck table: a parameter compared across all documents that report it."""

    name: str  # Korean display label, e.g. "정격출력"
    key: str  # canonical key, e.g. "Power" — stable identifier across languages
    sources: list[ParameterSourceValue]
    status: str  # "match" | "mismatch" | "partial"


class EquipmentSummary(BaseModel):
    id: int
    tag: str
    equipment_type: str
    document_count: int
    issue_count: int
    max_severity: str | None = None
    top_issue_label: str | None = None  # 가장 높은 위험도 이슈의 한 줄 요약 (예: "정격출력 불일치")


class EquipmentDetail(BaseModel):
    id: int
    tag: str
    equipment_type: str
    parameters: list[ParameterRow]
    issues: list["IssueOut"]


class IssueEvidenceItem(BaseModel):
    document: str
    document_id: int | None = None
    location: str | None = None
    value: str
    unit: str | None = None
    raw_snippet: str | None = None


DISPOSITION_VALUES = ("open", "intentional", "action_required", "resolved")


class IssueReviewIn(BaseModel):
    """Payload for PATCH /api/issues/{id}/review — the reviewing engineer's decision.
    Every field is optional so the frontend can PATCH just the part that changed."""

    disposition: str | None = None
    review_comment: str | None = None
    reviewed_by: str | None = None


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    equipment_id: int | None = None
    equipment_tag: str | None = None
    parameter_name: str | None = None
    parameter_label: str | None = None
    issue_type: str
    severity: str
    title: str
    description: str
    reasoning: str
    evidence: list[IssueEvidenceItem]
    impact_items: list[str]
    status: str
    disposition: str
    review_comment: str | None = None
    reviewed_by: str | None = None
    reviewed_at: dt.datetime | None = None
    created_at: dt.datetime


class DashboardOut(BaseModel):
    project_id: int
    project_name: str
    mode: str  # "demo" | "live"
    document_count: int
    equipment_count: int
    issue_count: int
    high_risk_count: int
    medium_count: int
    low_count: int
    info_count: int
    reviewed_count: int  # 검토가 끝난(open이 아닌) 이슈 수
    open_count: int  # 아직 검토 전인 이슈 수
    review_progress_percent: int
    severity_breakdown: list[dict]


class DemoLoadOut(BaseModel):
    project_id: int
    message: str
