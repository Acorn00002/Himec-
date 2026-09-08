"""Generates the human-readable "AI Reasoning" paragraph for an already-decided issue.

The severity and impact list are NOT decided here — they come from
services/issue_rules.py before this module is ever called. This function only asks
Gemini to explain, in plain engineering language, why that severity makes sense given
the facts. If Gemini is unavailable or fails, a deterministic template fallback keeps
the app fully usable without an API key.
"""

from __future__ import annotations

import logging

from app.services.ai.llm_client import llm_client
from app.services.crosscheck_basic import ParameterComparison

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an engineering review assistant. You are given facts about a \
data mismatch already found by deterministic comparison code, including its severity \
and likely impact — both already decided by rules, not by you. Write a short (2-3 \
sentence) Korean paragraph explaining WHY this mismatch matters from an engineering \
standpoint, grounded only in the given facts. Do not restate the severity level as a \
label; do not invent numbers, documents, or causes not given to you. Do not suggest a \
resolution or say which value is correct — this system only surfaces discrepancies for \
a human engineer to judge."""


def _facts_prompt(tag: str, comparison: ParameterComparison, severity: str, impact_items: list[str]) -> str:
    values = "; ".join(
        f"{s.document_name}: {s.value}{(' ' + s.unit) if s.unit else ''}" for s in comparison.sources
    )
    return (
        f"TAG: {tag}\n"
        f"Parameter: {comparison.name}\n"
        f"Values by document: {values}\n"
        f"Deviation note: {comparison.reason}\n"
        f"Decided severity: {severity}\n"
        f"Potential impact areas: {', '.join(impact_items)}"
    )


def _fallback_reasoning(comparison: ParameterComparison, severity: str, impact_items: list[str]) -> str:
    return (
        f"동일 TAG의 {comparison.name} 값이 문서 간 허용 오차를 초과하여 불일치합니다. "
        f"{comparison.reason or ''} 이 파라미터는 {', '.join(impact_items[:3])} 등에 영향을 줄 수 있어 "
        f"{severity} 위험도로 분류했습니다."
    ).strip()


def generate_reasoning(tag: str, comparison: ParameterComparison, severity: str, impact_items: list[str]) -> str:
    if not llm_client.is_configured:
        logger.info("SKIP Gemini reasoning for %s / %s: GEMINI_API_KEY not configured", tag, comparison.name)
        return _fallback_reasoning(comparison, severity, impact_items)
    try:
        logger.info("CALLING Gemini reasoning for %s / %s", tag, comparison.name)
        prompt = _facts_prompt(tag, comparison, severity, impact_items)
        text = llm_client.complete(SYSTEM_PROMPT, prompt, max_output_tokens=2048)
        return text.strip() or _fallback_reasoning(comparison, severity, impact_items)
    except Exception:
        logger.exception("Gemini reasoning generation FAILED for %s / %s", tag, comparison.name)
        return _fallback_reasoning(comparison, severity, impact_items)
