"""Dependency providers (single shared clients, wired into services)."""
from functools import lru_cache

import redis
from openai import OpenAI
from qdrant_client import QdrantClient

from app.core.config import Settings, get_settings
from app.services.booking import BookingService
from app.services.embeddings import EmbeddingService
from app.services.ingestion import IngestionService
from app.services.memory import ChatMemory
from app.services.rag import RAGService
from app.services.vector_store import VectorStore


@lru_cache
def get_embedder() -> EmbeddingService:
    s = get_settings()
    return EmbeddingService(OpenAI(api_key=s.openai_api_key, base_url=s.openai_base_url), s)


@lru_cache
def get_vector_store() -> VectorStore:
    s: Settings = get_settings()
    return VectorStore(QdrantClient(url=s.qdrant_url), s)


@lru_cache
def get_ingestion_service() -> IngestionService:
    return IngestionService(get_embedder(), get_vector_store())


@lru_cache
def get_rag_service() -> RAGService:
    s = get_settings()
    memory = ChatMemory(redis.Redis.from_url(s.redis_url, decode_responses=True), s)
    return RAGService(
        llm=OpenAI(api_key=s.openai_api_key, base_url=s.openai_base_url),
        embedder=get_embedder(),
        vector_store=get_vector_store(),
        memory=memory,
        booking_service=BookingService(),
        settings=s,
    )
