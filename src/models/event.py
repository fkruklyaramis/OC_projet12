from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(500), nullable=False)
    attendees = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    # Dates
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # Relations
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    support_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations ORM
    contract = relationship("Contract", back_populates="events")
    support_contact = relationship("User", foreign_keys=[support_contact_id])

    def __repr__(self):
        return f"<Event(id={self.id}, name={self.name}, " \
               f"contract_id={self.contract_id}, support_id={self.support_contact_id})>"

    @property
    def duration_days(self) -> int:
        return (self.end_date.date() - self.start_date.date()).days + 1

    @property
    def client(self):
        return self.contract.client if self.contract else None
