"""API 1: Document ingestion."""
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_ingestion_service
from app.db.session import get_db
from app.schemas.ingestion import DocumentResponse
from app.services.chunking import ChunkStrategy
from app.services.document_parser import UnsupportedFileTypeError
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/api/v1/documents", tags=["Ingestion"])


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: Annotated[UploadFile, File(description=".pdf or .txt")],
    strategy: Annotated[ChunkStrategy, Form()],
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> DocumentResponse:
    content = file.file.read()
    try:
        document = service.ingest(db, file.filename or "unknown", content, strategy)
    except (UnsupportedFileTypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DocumentResponse.model_validate(document)
