"""Custom RAG pipeline (no RetrievalQAChain): retrieve -> prompt -> LLM (+ booking tool)."""
import json
import logging
import uuid
from datetime import date
from typing import Any

from openai import OpenAI
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.chat import BookingRequest, ChatRequest, ChatResponse
from app.services.booking import BookingService
from app.services.embeddings import EmbeddingService
from app.services.memory import ChatMemory
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

BOOKING_KEYWORDS = ("book", "schedule", "appointment", "reserve")

BOOKING_TOOL = {
    "type": "function",
    "function": {
        "name": "book_interview",
        "description": (
            "Book an interview. Call ONLY when the user wants to book AND has given "
            "name, email, date and time. Otherwise ask for the missing details."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "time": {"type": "string", "description": "HH:MM, 24-hour"},
            },
            "required": ["name", "email", "date", "time"],
        },
    },
}

SYSTEM_PROMPT = """You are a helpful assistant.
Answer questions using ONLY the context below. If the answer is not in the context, say you don't know.
You can also book interviews: collect the user's name, email, date and time, then call book_interview.
Never call book_interview until the user has provided all four details. Never guess or invent values.
Today's date is {today}.

Context:
{context}"""


class RAGService:
    def __init__(
        self,
        llm: OpenAI,
        embedder: EmbeddingService,
        vector_store: VectorStore,
        memory: ChatMemory,
        booking_service: BookingService,
        settings: Settings,
    ) -> None:
        self._llm = llm
        self._embedder = embedder
        self._vector_store = vector_store
        self._memory = memory
        self._booking = booking_service
        self._settings = settings

    def chat(self, db: Session, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())
        history = self._memory.get_history(session_id)

        # 1. Retrieve: include the previous user turn so follow-ups still work.
        previous_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        query_vector = self._embedder.embed_query(f"{previous_user}\n{request.message}".strip())
        chunks = self._vector_store.search(query_vector, self._settings.top_k)
        context = "\n\n".join(c.text for c in chunks) or "No documents found."

        # 2. Build prompt: system + Redis history + new question.
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(today=date.today(), context=context)},
            *history,
            {"role": "user", "content": request.message},
        ]

        # 3. Call LLM. The booking tool is offered only when booking is being discussed.
        extra: dict[str, Any] = {}
        if self._wants_booking(request.message, history):
            extra["tools"] = [BOOKING_TOOL]

        response = self._llm.chat.completions.create(
            model=self._settings.chat_model,
            messages=messages,  # type: ignore[arg-type]
            **extra,
        )
        message = response.choices[0].message
        answer = message.content or ""
        booking_id: int | None = None

        if message.tool_calls:
            answer, booking_id = self._handle_booking(
                db, session_id, message.tool_calls[0].function.arguments
            )

        # 4. Save turn to memory.
        self._memory.add_message(session_id, "user", request.message)
        self._memory.add_message(session_id, "assistant", answer)

        return ChatResponse(
            session_id=session_id,
            answer=answer,
            sources=sorted({c.filename for c in chunks}),
            booking_id=booking_id,
        )

    @staticmethod
    def _wants_booking(message: str, history: list[dict[str, str]]) -> bool:
        """Offer the booking tool only if booking came up in the last few user messages."""
        recent_user = [m["content"] for m in history if m["role"] == "user"][-2:]
        text = " ".join([message, *recent_user]).lower()
        return any(keyword in text for keyword in BOOKING_KEYWORDS)

    def _handle_booking(self, db: Session, session_id: str, raw_args: str) -> tuple[str, int | None]:
        logger.warning("Booking tool args: %s", raw_args)
        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            return "I couldn't read the booking details. Please send your name, email, date and time again.", None

        labels = {"name": "name", "email": "email", "date": "date (YYYY-MM-DD)", "time": "time (HH:MM)"}
        missing = [label for key, label in labels.items() if not str(args.get(key, "")).strip()]
        if missing:
            return f"To book your interview I still need your: {', '.join(missing)}.", None

        try:
            data = BookingRequest(
                name=args["name"],
                email=args["email"],
                interview_date=args["date"],
                interview_time=args["time"],
            )
        except ValidationError as exc:
            fields = sorted({str(err["loc"][0]) for err in exc.errors()})
            return (
                f"These booking details look invalid: {', '.join(fields)}. "
                "Please re-send them (date as YYYY-MM-DD, time as HH:MM, a real email).",
                None,
            )

        booking = self._booking.create(db, session_id, data)
        return (
            f"Interview booked for {data.name} on {data.interview_date} at "
            f"{data.interview_time.strftime('%H:%M')}. Confirmation will be sent to {data.email}.",
            booking.id,
        )
