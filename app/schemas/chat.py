"""Schemas for the conversational RAG API."""
from datetime import date, time

from pydantic import BaseModel, EmailStr, Field


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, description="Omit to start a new conversation")
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[str] = []
    booking_id: int | None = None


class BookingRequest(BaseModel):
    """Validated interview booking details extracted by the LLM."""

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    interview_date: date
    interview_time: time
