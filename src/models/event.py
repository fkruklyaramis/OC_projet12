from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base
from datetime import datetime


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    support_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False)
    location = Column(String(500), nullable=False)
    attendees = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    contract = relationship("Contract", back_populates="events", foreign_keys=[contract_id])
    support_contact = relationship("User", back_populates="events",
                                   foreign_keys=[support_contact_id])

    def __repr__(self):
        return f"<Event(id={self.id}, name={self.name}, attendees={self.attendees})>"

    @property
    def has_support_assigned(self) -> bool:
        return self.support_contact_id is not None

    @property
    def is_upcoming(self) -> bool:
        return self.start_date > datetime.now()

    @property
    def is_ongoing(self) -> bool:
        now = datetime.now()
        return self.start_date <= now <= self.end_date

    @property
    def is_past(self) -> bool:
        return self.end_date < datetime.now()

    @property
    def duration_hours(self) -> float:
        duration = self.end_date - self.start_date
        return duration.total_seconds() / 3600

    @property
    def client_name(self) -> str:
        return self.contract.client.full_name if self.contract and self.contract.client else "N/A"
