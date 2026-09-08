"""Phase 12 — report generation. Renders the same data the UI shows (dashboard stats +
issues with evidence/impact/reasoning) into a PDF, so a reviewing engineer has something
to print/archive/forward. No new judgments are made here — this is a rendering step."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.db import models
from app.services.ai.report_summary import generate_executive_summary

# Base-14 PDF fonts (Helvetica, Times, ...) have no Korean glyphs. reportlab ships
# predefined CID font metrics for the standard Asian fonts — no font file to bundle,
# and every mainstream PDF viewer substitutes an installed CJK font for these names.
KOREAN_FONT = "HYSMyeongJo-Medium"
pdfmetrics.registerFont(UnicodeCIDFont(KOREAN_FONT))

SEVERITY_COLORS = {
    "HIGH": colors.HexColor("#d03b3b"),
    "MEDIUM": colors.HexColor("#ec835a"),
    "LOW": colors.HexColor("#c98500"),
    "INFO": colors.HexColor("#0ca30c"),
}
SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
SEVERITY_LABELS = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음", "INFO": "참고"}

DISPOSITION_LABELS = {
    "open": "미검토",
    "intentional": "의도된 차이 (Design Margin)",
    "action_required": "조치 필요",
    "resolved": "조치 완료",
}
DISPOSITION_COLORS = {
    "open": colors.HexColor("#6b7280"),
    "intentional": colors.HexColor("#2563eb"),
    "action_required": colors.HexColor("#d03b3b"),
    "resolved": colors.HexColor("#0a7a0a"),
}


def _stats_for(db: Session, project: models.Project) -> dict:
    document_count = db.query(models.Document).filter(models.Document.project_id == project.id).count()
    equipment_count = db.query(models.Equipment).filter(models.Equipment.project_id == project.id).count()
    issues = db.query(models.Issue).filter(models.Issue.project_id == project.id).all()
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for i in issues:
        if i.severity in counts:
            counts[i.severity] += 1
    disposition_counts = {"open": 0, "intentional": 0, "action_required": 0, "resolved": 0}
    for i in issues:
        key = i.disposition or "open"
        if key in disposition_counts:
            disposition_counts[key] += 1
    return {
        "document_count": document_count,
        "equipment_count": equipment_count,
        "issue_count": len(issues),
        "high_risk_count": counts["HIGH"],
        "medium_count": counts["MEDIUM"],
        "low_count": counts["LOW"],
        "info_count": counts["INFO"],
        "reviewed_count": len(issues) - disposition_counts["open"],
        "disposition_counts": disposition_counts,
    }, issues


def generate_report_pdf(db: Session, project: models.Project) -> bytes:
    stats, issues = _stats_for(db, project)
    issues = sorted(issues, key=lambda i: SEVERITY_ORDER.get(i.severity, 99))
    high_titles = [i.title for i in issues if i.severity == "HIGH"]

    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = KOREAN_FONT  # every style may contain Korean text somewhere in the report

    title_style = styles["Title"]
    h3_style = styles["Heading3"]
    h4_style = styles["Heading4"]
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("Body", parent=styles["BodyText"], leading=14)
    small_style = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8, textColor=colors.grey, leading=11)
    disclaimer_style = ParagraphStyle(
        "Disclaimer", parent=styles["BodyText"], fontSize=9, textColor=colors.HexColor("#8f6000"),
        backColor=colors.HexColor("#fff8e6"), borderPadding=6, leading=13,
    )
    review_style = ParagraphStyle(
        "Review", parent=styles["BodyText"], fontSize=8.5, textColor=colors.HexColor("#1f2937"),
        backColor=colors.HexColor("#eef2ff"), borderPadding=6, leading=12,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"{project.name} — Engineering CrossCheck Report",
    )

    story = []
    story.append(Paragraph("설계 문서 교차검증 리포트", title_style))
    story.append(Paragraph("Engineering CrossCheck Report", h4_style))
    story.append(Paragraph(project.name, h3_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "이 리포트는 AI 검토 결과이며 설계 승인 문서가 아닙니다. 모든 발견 사항은 근거 문서와 함께 제시되며, "
        "최종 설계 판단은 담당 엔지니어의 확인이 필요합니다.",
        disclaimer_style,
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("요약 (Summary)", h2_style))
    summary_table = Table(
        [
            ["문서", "설비", "총 이슈", "높음", "중간", "낮음", "참고"],
            [
                stats["document_count"], stats["equipment_count"], stats["issue_count"],
                stats["high_risk_count"], stats["medium_count"], stats["low_count"], stats["info_count"],
            ],
        ],
        hAlign="LEFT",
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2ef")),
        ("FONTNAME", (0, 0), (-1, -1), KOREAN_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddad2")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("엔지니어 검토 현황 (Engineer Review Status)", h2_style))
    dc = stats["disposition_counts"]
    review_table = Table(
        [
            ["검토 완료", "미검토", "의도된 차이", "조치 필요", "조치 완료"],
            [
                stats["reviewed_count"], dc["open"], dc["intentional"],
                dc["action_required"], dc["resolved"],
            ],
        ],
        hAlign="LEFT",
    )
    review_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2ef")),
        ("FONTNAME", (0, 0), (-1, -1), KOREAN_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddad2")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(review_table)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "‘의도된 차이’로 분류된 항목은 담당 엔지니어가 설계상 의도된 것으로 확인한 불일치이며, "
        "검토 의견은 각 Finding에 함께 기재됩니다.",
        small_style,
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("총평 (Executive Summary)", h2_style))
    exec_summary = generate_executive_summary(project.name, stats, high_titles)
    story.append(Paragraph(exec_summary, body_style))

    story.append(Paragraph(f"발견 사항 (Findings) — {len(issues)}건", h2_style))
    if not issues:
        story.append(Paragraph("발견된 이슈가 없습니다.", body_style))

    for issue in issues:
        block = []
        sev_color = SEVERITY_COLORS.get(issue.severity, colors.grey)
        sev_label = SEVERITY_LABELS.get(issue.severity, issue.severity)
        header = f'<font color="{sev_color.hexval()}"><b>[{sev_label}]</b></font> {issue.title}'
        if issue.equipment and issue.equipment.tag:
            header = f"<b>{issue.equipment.tag}</b> — " + header
        block.append(Paragraph(header, h4_style))
        block.append(Paragraph(issue.description, body_style))

        if issue.evidence:
            rows = [["문서", "위치", "값"]]
            for e in issue.evidence:
                value = f"{e.get('value', '')} {e.get('unit') or ''}".strip()
                rows.append([e.get("document", ""), e.get("location") or "-", value])
            evidence_table = Table(rows, hAlign="LEFT", colWidths=[55 * mm, 40 * mm, 35 * mm])
            evidence_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2ef")),
                ("FONTNAME", (0, 0), (-1, -1), KOREAN_FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddad2")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            block.append(Spacer(1, 4))
            block.append(evidence_table)

        if issue.impact_items:
            block.append(Spacer(1, 4))
            block.append(Paragraph(f"<b>영향 가능 항목:</b> {', '.join(issue.impact_items)}", small_style))

        block.append(Spacer(1, 4))
        block.append(Paragraph(f"<b>AI 분석 근거:</b> {issue.reasoning}", small_style))

        disposition = issue.disposition or "open"
        if disposition != "open" or issue.review_comment:
            block.append(Spacer(1, 5))
            disp_color = DISPOSITION_COLORS.get(disposition, colors.grey)
            meta_bits = [
                f'<font color="{disp_color.hexval()}"><b>{DISPOSITION_LABELS.get(disposition, disposition)}</b></font>'
            ]
            if issue.reviewed_by:
                meta_bits.append(f"검토자: {issue.reviewed_by}")
            if issue.reviewed_at:
                meta_bits.append(issue.reviewed_at.strftime("%Y-%m-%d"))
            review_lines = "<b>엔지니어 검토 — </b>" + " · ".join(meta_bits)
            if issue.review_comment:
                review_lines += "<br/>" + issue.review_comment.replace("\n", "<br/>")
            block.append(Paragraph(review_lines, review_style))

        block.append(Spacer(1, 12))

        story.append(KeepTogether(block))

    doc.build(story)
    return buffer.getvalue()
