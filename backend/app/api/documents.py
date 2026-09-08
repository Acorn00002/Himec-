import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import UPLOAD_DIR
from app.db import models
from app.db.database import get_db
from app.schemas.schemas import DocumentOut, ExtractedChunkOut
from app.services.extraction_pipeline import extract_and_store
from app.services.parsing.dispatch import parse_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["documents"])

EXTENSION_TO_TYPE = {
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".csv": "csv",
    ".txt": "txt",
}


@router.get("/{project_id}/documents", response_model=list[DocumentOut])
def list_documents(project_id: int, db: Session = Depends(get_db)):
    return db.query(models.Document).filter(models.Document.project_id == project_id).all()


@router.post("/{project_id}/documents", response_model=DocumentOut)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    category: str = Form("other"),
    db: Session = Depends(get_db),
):
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    suffix = Path(file.filename).suffix.lower()
    doc_type = EXTENSION_TO_TYPE.get(suffix)
    if doc_type is None:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {suffix}")

    project_dir = UPLOAD_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    dest_path = project_dir / file.filename
    contents = await file.read()
    dest_path.write_bytes(contents)

    document = models.Document(
        project_id=project_id,
        filename=file.filename,
        doc_type=doc_type,
        category=category,
        status="uploaded",
        file_path=str(dest_path),
    )
    db.add(document)
    db.flush()

    try:
        chunks = parse_document(doc_type, str(dest_path))
        for order_index, chunk in enumerate(chunks):
            db.add(models.ExtractedChunk(
                document_id=document.id,
                location=chunk.location,
                content_type=chunk.content_type,
                text=chunk.text,
                order_index=order_index,
            ))
        if chunks:
            document.status = "parsed"
    except Exception:
        logger.exception("Failed to parse document %s (%s)", document.filename, doc_type)
        # Keep status "uploaded" — the file is safely stored even if parsing failed;
        # extraction can be retried later without re-uploading.
    db.flush()

    # Phase 9: ask Gemini to read the parsed chunks (or the image itself) and extract
    # TAG/parameter data points. No-ops gracefully if GEMINI_API_KEY isn't configured.
    if extract_and_store(db, project_id, document):
        document.status = "analyzed"

    db.commit()
    db.refresh(document)
    return document


@router.get("/{project_id}/documents/{document_id}/content", response_model=list[ExtractedChunkOut])
def get_document_content(project_id: int, document_id: int, db: Session = Depends(get_db)):
    document = db.query(models.Document).filter(
        models.Document.id == document_id, models.Document.project_id == project_id
    ).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document.extracted_chunks
