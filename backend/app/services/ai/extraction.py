"""Phase 9 — AI-assisted TAG and parameter extraction.

Turns the raw text chunks a document parser (Phase 8) produced — or, for images, the
image file itself via Gemini vision — into candidate (equipment TAG, parameter) data
points. This is the ONLY place in the app that asks an LLM to read engineering values;
everything downstream (unit conversion, match/mismatch comparison, severity) is
deterministic code in services/crosscheck_basic.py and services/issue_rules.py.

The model is instructed to extract only what is explicitly written and to cite the
exact source location for every value, so every extracted parameter can be traced back
to a page/sheet the same way the seeded demo data is (see services/demo_data.py).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.db import models
from app.services.ai.llm_client import llm_client

PARAMETER_VOCAB = [
    "Manufacturer", "Model", "Power", "Voltage", "Current", "RPM", "Efficiency",
    "Power Factor", "Frequency", "Cable Size", "Breaker Size", "Flow", "Pressure",
    "Temperature", "Insulation Class", "Protection Rating", "Dimension", "Weight",
]

EQUIPMENT_TYPE_HINTS = ["Motor", "Pump", "AHU", "Transformer", "Fan", "Compressor", "Valve", "Panel"]


class ExtractedParameter(BaseModel):
    name: str = Field(description="One of the controlled parameter vocabulary")
    value: str = Field(description="Numeric or text value, unit stripped out")
    unit: str | None = Field(default=None, description="Unit if the value is numeric, else null")
    location: str = Field(description="Copied verbatim from a [location: ...] marker in the input")
    raw_snippet: str = Field(description="Short verbatim quote from the source text as evidence")


class ExtractedEquipment(BaseModel):
    tag: str = Field(description="Equipment TAG exactly as written, e.g. M-101")
    equipment_type: str = Field(description="Equipment category, e.g. Motor, Pump, AHU")
    parameters: list[ExtractedParameter] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    equipment: list[ExtractedEquipment] = Field(default_factory=list)


SYSTEM_PROMPT = f"""You are an engineering document extraction agent for an industrial \
equipment cross-check system. You are given raw text extracted from ONE design \
document (a specification sheet, drawing, calculation, equipment list, or P&ID), or \
an image of one (a nameplate photo, scanned drawing, etc).

Extract every distinct piece of equipment mentioned by its TAG (e.g. "M-101", "P-101", \
"AHU-101") and, for each, only the parameters explicitly stated — never infer, \
calculate, round, or guess a value that is not written down. If nothing is stated for \
a parameter, omit it entirely rather than inventing a value.

The documents are often written in Korean or mixed Korean/English. Map every concept \
onto this English parameter vocabulary regardless of the source language (e.g. 정격출력 / \
출력 / Rated Output -> "Power"; 정격전압 -> "Voltage"; 제조사 / 제작사 -> "Manufacturer"; \
형식 / 모델 -> "Model"; 차단기 용량 / MCCB -> "Breaker Size"; 유량 / 풍량 -> "Flow"; \
양정 / 압력 -> "Pressure"). Use the closest name; skip anything not present in the source: \
{", ".join(PARAMETER_VOCAB)}.
Typical equipment types (normalize Korean too — 전동기->Motor, 펌프->Pump, 변압기->Transformer, \
송풍기->Fan, 압축기->Compressor): {", ".join(EQUIPMENT_TYPE_HINTS)} (use your best judgment for others).

For every parameter:
- Split the numeric value from its unit (value="15", unit="kW"). Leave unit null for \
unitless/text values such as Manufacturer or Model.
- Normalise units to plain ASCII: "m3/h" not "m³/h", "mm2" not "mm²" or "SQMM", "C" not "℃".
- For Cable Size, report ONLY the conductor cross-section number as the value and "mm2" \
as the unit. Ignore conductor-count / arrangement prefixes such as "4C x", "3C+E", \
"1C", "4/C" (e.g. "4C x 25 SQMM" -> value="25", unit="mm2").
- For Breaker Size, report the trip rating in amps (e.g. "MCCB 50AF/40AT" -> value="40", \
unit="A"; "40 A" -> value="40", unit="A").
- location MUST be copied exactly from one of the "[location: ...]" markers in the \
text input. For an image input (no location markers given), use "image".
- raw_snippet is a short verbatim quote (under 20 words) from the source that supports \
the extracted value.

If the document does not mention any equipment TAG, return an empty equipment list."""


def _build_text_prompt(document_filename: str, chunks: list[models.ExtractedChunk]) -> str:
    parts = [f"Document: {document_filename}\n"]
    for chunk in chunks:
        parts.append(f"[location: {chunk.location}]\n{chunk.text}\n")
    return "\n".join(parts)


def extract_from_chunks(document_filename: str, chunks: list[models.ExtractedChunk]) -> ExtractionResult:
    if not chunks:
        return ExtractionResult(equipment=[])
    prompt = _build_text_prompt(document_filename, chunks)
    return llm_client.complete_structured(SYSTEM_PROMPT, prompt, ExtractionResult)


def extract_from_image(document_filename: str, image_path: str) -> ExtractionResult:
    prompt = f"Document: {document_filename}\nThis is an image of an equipment nameplate, drawing, or scan."
    return llm_client.complete_structured(SYSTEM_PROMPT, prompt, ExtractionResult, image_path=image_path)


_NUMERIC_UNIT_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([^\d\s]*)\s*$")


def parse_numeric(value: str) -> float | None:
    """Best-effort numeric parse. The model is instructed to already separate value
    from unit, but this guards against a stray unit slipping into `value` (e.g. "15kW")."""
    try:
        return float(value)
    except ValueError:
        pass
    match = _NUMERIC_UNIT_RE.match(value)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None
