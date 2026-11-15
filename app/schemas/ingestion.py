"""Schemas for the ingestion API."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    chunking_strategy: str
    chunk_count: int
    created_at: datetime
