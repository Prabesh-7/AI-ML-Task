"""Orchestrates: parse -> chunk -> embed -> store vectors -> save metadata."""
from sqlalchemy.orm import Session

from app.db.models import Document
from app.services.chunking import ChunkStrategy, chunk_text
from app.services.document_parser import extract_text
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


class IngestionService:
    def __init__(self, embedder: EmbeddingService, vector_store: VectorStore) -> None:
        self._embedder = embedder
        self._vector_store = vector_store

    def ingest(self, db: Session, filename: str, content: bytes, strategy: ChunkStrategy) -> Document:
        text = extract_text(filename, content)
        chunks = chunk_text(text, strategy)
        if not chunks:
            raise ValueError("No text could be extracted from the file")

        vectors = self._embedder.embed_texts(chunks)

        document = Document(
            filename=filename,
            file_type=filename.rsplit(".", 1)[-1].lower(),
            chunking_strategy=strategy.value,
            chunk_count=len(chunks),
        )
        db.add(document)
        db.flush()  # generates document.id

        self._vector_store.add_chunks(document.id, filename, chunks, vectors)
        db.commit()
        return document
