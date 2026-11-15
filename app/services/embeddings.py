"""Create embeddings with OpenAI."""
from openai import OpenAI

from app.core.config import Settings


class EmbeddingService:
    def __init__(self, client: OpenAI, settings: Settings) -> None:
        self._client = client
        self._model = settings.embedding_model

    def embed_texts(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self._client.embeddings.create(model=self._model, input=batch)
            vectors.extend(item.embedding for item in response.data)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]
