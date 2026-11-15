"""Qdrant vector store wrapper."""
import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import Settings


@dataclass
class RetrievedChunk:
    text: str
    filename: str
    score: float


class VectorStore:
    def __init__(self, client: QdrantClient, settings: Settings) -> None:
        self._client = client
        self._collection = settings.qdrant_collection
        self._dim = settings.embedding_dim

    def ensure_collection(self) -> None:
        if not self._client.collection_exists(self._collection):
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._dim, distance=Distance.COSINE),
            )

    def add_chunks(
        self, document_id: str, filename: str, chunks: list[str], vectors: list[list[float]]
    ) -> None:
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": index,
                    "text": chunk,
                },
            )
            for index, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        self._client.upsert(collection_name=self._collection, points=points)

    def search(self, vector: list[float], top_k: int) -> list[RetrievedChunk]:
        result = self._client.query_points(
            collection_name=self._collection, query=vector, limit=top_k, with_payload=True
        )
        return [
            RetrievedChunk(
                text=str(point.payload["text"]),
                filename=str(point.payload["filename"]),
                score=point.score,
            )
            for point in result.points
            if point.payload
        ]
