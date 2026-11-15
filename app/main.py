"""FastAPI application entry point."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.deps import get_vector_store
from app.api.routes import chat, ingestion
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    get_vector_store().ensure_collection()
    yield


app = FastAPI(title="RAG Backend", lifespan=lifespan)
app.include_router(ingestion.router)
app.include_router(chat.router)
