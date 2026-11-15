# RAG Backend (FastAPI + Qdrant + Redis + PostgreSQL)

Two REST APIs:
1. **Document ingestion** - upload .pdf/.txt, extract text, chunk (`fixed` or `paragraph`), embed, store vectors in Qdrant and metadata in PostgreSQL.
2. **Conversational RAG** - custom retrieval pipeline (no RetrievalQAChain), Redis chat memory, multi-turn chat, LLM-driven interview booking stored in PostgreSQL.

No FAISS/Chroma, no UI.

## Run
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d                  # Postgres, Redis, Qdrant
ollama pull llama3.1 && ollama pull nomic-embed-text
uvicorn app.main:app --reload
```
Open http://localhost:8000/docs

## Endpoints
- `POST /api/v1/documents/upload` - form fields: `file`, `strategy` (`fixed` | `paragraph`)
- `POST /api/v1/chat` - JSON: `message`, optional `session_id`

## Design notes
- Layers: routes -> services -> stores; dependencies wired in `app/api/deps.py`.
- Works with OpenAI or any OpenAI-compatible server (e.g. Ollama) via `OPENAI_BASE_URL`.
- The booking tool is exposed to the LLM only when booking intent is detected; details are validated with Pydantic before saving.
- Chat memory: one Redis list per session, trimmed to the last N messages, with a TTL.
