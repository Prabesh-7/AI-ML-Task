"""Persist interview bookings."""
from sqlalchemy.orm import Session

from app.db.models import Booking
from app.schemas.chat import BookingRequest


class BookingService:
    def create(self, db: Session, session_id: str, data: BookingRequest) -> Booking:
        booking = Booking(
            session_id=session_id,
            name=data.name,
            email=str(data.email),
            interview_date=data.interview_date,
            interview_time=data.interview_time,
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking
