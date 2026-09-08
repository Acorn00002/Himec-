"""Wires Phase 9 (Gemini extraction) output into the normalized data model —
find-or-create Equipment by TAG, then create ParameterValue rows tied back to the
source document. Called right after a document is parsed (or, for images, right
after upload) so Equipment/ParameterValue are always populated before a user asks
for CrossCheck to run.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db import models
from app.services.ai.extraction import ExtractionResult, extract_from_chunks, extract_from_image, parse_numeric
from app.services.ai.llm_client import llm_client
from app.services.parameters import (
    canonical_equipment_type,
    canonical_key,
    clean_cable_value,
    normalize_unit,
)

logger = logging.getLogger(__name__)


def _get_or_create_equipment(db: Session, project_id: int, tag: str, equipment_type: str) -> models.Equipment:
    tag = tag.strip()
    existing = db.query(models.Equipment).filter(
        models.Equipment.project_id == project_id, models.Equipment.tag == tag
    ).first()
    if existing:
        return existing
    equipment = models.Equipment(project_id=project_id, tag=tag, equipment_type=equipment_type)
    db.add(equipment)
    db.flush()
    return equipment


def _store_result(db: Session, project_id: int, document: models.Document, result: ExtractionResult) -> int:
    count = 0
    for extracted_equipment in result.equipment:
        if not extracted_equipment.tag.strip():
            continue
        equipment = _get_or_create_equipment(
            db, project_id, extracted_equipment.tag,
            canonical_equipment_type(extracted_equipment.equipment_type),
        )
        for param in extracted_equipment.parameters:
            key = canonical_key(param.name)
            value, unit = param.value, param.unit
            # Cable cross-section frequently arrives as "4C x 25 SQMM" — reduce to "25 mm2"
            # so it compares as a value, not free text.
            if key == "Cable Size":
                cleaned_value, cleaned_unit = clean_cable_value(value)
                if cleaned_unit:
                    value, unit = cleaned_value, cleaned_unit
            unit = normalize_unit(unit)
            db.add(models.ParameterValue(
                equipment_id=equipment.id,
                document_id=document.id,
                name=key,
                value=value,
                numeric_value=parse_numeric(value),
                unit=unit,
                location=param.location,
                raw_snippet=param.raw_snippet,
            ))
            count += 1
    return count


def extract_and_store(db: Session, project_id: int, document: models.Document) -> bool:
    """Returns True if extraction ran and the document should be marked "analyzed"."""
    if not llm_client.is_configured:
        logger.info("SKIP Gemini extraction for %s: GEMINI_API_KEY not configured", document.filename)
        return False

    try:
        if document.doc_type == "image":
            logger.info("CALLING Gemini vision extraction for %s (image)", document.filename)
            result = extract_from_image(document.filename, document.file_path)
        else:
            chunks = list(document.extracted_chunks)
            if not chunks:
                logger.info("SKIP Gemini extraction for %s: no parsed text chunks", document.filename)
                return False
            logger.info(
                "CALLING Gemini text extraction for %s (%d chunk(s))", document.filename, len(chunks)
            )
            result = extract_from_chunks(document.filename, chunks)
    except Exception:
        logger.exception("Gemini extraction FAILED for document %s", document.filename)
        return False

    count = _store_result(db, project_id, document, result)
    tags = [e.tag for e in result.equipment]
    logger.info(
        "Gemini extraction OK for %s: %d equipment (%s), %d parameter value(s)",
        document.filename, len(result.equipment), tags, count,
    )
    return True
