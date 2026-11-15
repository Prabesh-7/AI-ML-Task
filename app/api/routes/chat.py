"""API 2: Conversational RAG + interview booking."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_rag_service
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import RAGService

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    service: Annotated[RAGService, Depends(get_rag_service)],
) -> ChatResponse:
    return service.chat(db, request)
