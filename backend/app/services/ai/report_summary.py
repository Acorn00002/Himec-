"""Generates the one-paragraph executive summary at the top of the exported report.

Same non-negotiable as issue_reasoning.py: the facts (counts, which issues are HIGH,
what they're about) are computed deterministically before this is called. The LLM only
turns them into readable prose — it cannot add a finding that isn't already in the list.
"""

from __future__ import annotations

import logging

from app.services.ai.llm_client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an engineering review assistant writing the executive \
summary of a design cross-check report. You are given exact counts and a list of the \
highest-severity findings, already computed by the system. Write 3-4 sentences in \
Korean summarizing the review for an engineering manager: how many documents/equipment \
were checked, how many issues were found, and what the most urgent items are. Do not \
invent findings, numbers, or documents beyond what is given. Do not recommend a fix or \
declare anything resolved — end by noting that engineer review is still required."""


def _fallback_summary(project_name: str, stats: dict, high_titles: list[str]) -> str:
    lead = (
        f"{project_name} 프로젝트에서 문서 {stats['document_count']}건, 설비 {stats['equipment_count']}건을 "
        f"검토한 결과 총 {stats['issue_count']}건의 이슈가 발견되었습니다 (HIGH {stats['high_risk_count']}건, "
        f"MEDIUM {stats['medium_count']}건, LOW {stats['low_count']}건, INFO {stats['info_count']}건)."
    )
    if high_titles:
        lead += " 우선 검토가 필요한 HIGH 위험도 항목: " + "; ".join(high_titles[:3]) + "."
    lead += " 모든 결과는 AI 검토 의견이며 최종 판단은 담당 엔지니어의 확인이 필요합니다."
    return lead


def generate_executive_summary(project_name: str, stats: dict, high_titles: list[str]) -> str:
    if not llm_client.is_configured:
        logger.info("SKIP Gemini executive summary for %s: GEMINI_API_KEY not configured", project_name)
        return _fallback_summary(project_name, stats, high_titles)
    try:
        logger.info("CALLING Gemini executive summary for %s", project_name)
        prompt = (
            f"Project: {project_name}\n"
            f"Documents: {stats['document_count']}, Equipment: {stats['equipment_count']}\n"
            f"Issues — HIGH: {stats['high_risk_count']}, MEDIUM: {stats['medium_count']}, "
            f"LOW: {stats['low_count']}, INFO: {stats['info_count']}\n"
            f"HIGH severity finding titles: {high_titles}"
        )
        text = llm_client.complete(SYSTEM_PROMPT, prompt, max_output_tokens=3072)
        return text.strip() or _fallback_summary(project_name, stats, high_titles)
    except Exception:
        logger.exception("Gemini executive summary generation failed for project %s", project_name)
        return _fallback_summary(project_name, stats, high_titles)
