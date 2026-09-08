import datetime as dt

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    documents: Mapped[list["Document"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    equipment: Mapped[list["Equipment"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    issues: Mapped[list["Issue"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    filename: Mapped[str] = mapped_column(String(255))
    doc_type: Mapped[str] = mapped_column(String(20))  # pdf | image | xlsx | csv | txt
    category: Mapped[str] = mapped_column(String(30))  # spec | drawing | calculation | equipment_list | pid | other
    status: Mapped[str] = mapped_column(String(20), default="uploaded")  # uploaded | parsed | analyzed
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="documents")
    parameter_values: Mapped[list["ParameterValue"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    extracted_chunks: Mapped[list["ExtractedChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="ExtractedChunk.order_index"
    )


class ExtractedChunk(Base):
    """Raw content pulled out of a document by the deterministic parser (Phase 8) —
    one row per page/sheet/section. This is the "raw extracted content" stage of the
    pipeline (section 13): original file -> parser -> raw extracted content -> ...
    AI extraction (Phase 9) reads these chunks; it never re-parses the original file."""

    __tablename__ = "extracted_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    location: Mapped[str] = mapped_column(String(100))  # e.g. "p.3" or "Sheet1"
    content_type: Mapped[str] = mapped_column(String(20))  # text | table
    text: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(default=0)

    document: Mapped["Document"] = relationship(back_populates="extracted_chunks")


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    tag: Mapped[str] = mapped_column(String(50), index=True)
    equipment_type: Mapped[str] = mapped_column(String(50))  # Motor | Pump | AHU | ...

    project: Mapped["Project"] = relationship(back_populates="equipment")
    parameter_values: Mapped[list["ParameterValue"]] = relationship(back_populates="equipment", cascade="all, delete-orphan")
    issues: Mapped[list["Issue"]] = relationship(back_populates="equipment", cascade="all, delete-orphan")


class ParameterValue(Base):
    """A single (equipment, parameter, source document) data point — the atomic unit that
    cross-check compares across documents. Multiple rows can share equipment_id + name
    when several documents report the same parameter."""

    __tablename__ = "parameter_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    name: Mapped[str] = mapped_column(String(50))  # power, voltage, current, rpm, ...
    value: Mapped[str] = mapped_column(String(100))  # raw display value, e.g. "15", "ABB"
    numeric_value: Mapped[float | None] = mapped_column(nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "p.12" or "Sheet1!B4"
    raw_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)

    equipment: Mapped["Equipment"] = relationship(back_populates="parameter_values")
    document: Mapped["Document"] = relationship(back_populates="parameter_values")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    equipment_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id"), nullable=True)
    parameter_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(30))  # value_mismatch | unit_mismatch | missing | spec_mismatch | abnormal_value | calc_mismatch
    severity: Mapped[str] = mapped_column(String(10))  # INFO | LOW | MEDIUM | HIGH
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    reasoning: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list] = mapped_column(JSON, default=list)  # [{document, location, value, unit, raw_snippet}]
    impact_items: Mapped[list] = mapped_column(JSON, default=list)  # ["Cable Sizing", "Breaker Selection", ...]
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | reviewed | resolved

    # ---- Human-in-the-Loop review state (set by the reviewing engineer, not by the AI) ----
    # disposition: the engineer's call on WHY the values differ / what to do about it.
    #   open            – not yet reviewed
    #   intentional     – 의도된 차이 (design margin / spec difference on purpose)
    #   action_required – 조치 필요 (a real error that must be corrected)
    #   resolved        – 조치 완료 (the underlying documents have been fixed)
    disposition: Mapped[str] = mapped_column(String(20), default="open")
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)  # 검토 의견 / 예외 사유
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="issues")
    equipment: Mapped["Equipment"] = relationship(back_populates="issues")
