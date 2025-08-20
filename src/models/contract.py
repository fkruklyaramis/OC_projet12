from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base
from decimal import Decimal


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    commercial_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    remaining_amount = Column(Numeric(10, 2), nullable=False)
    is_signed = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    client = relationship("Client", back_populates="contracts", foreign_keys=[client_id])
    commercial_contact = relationship("User", back_populates="contracts",
                                      foreign_keys=[commercial_contact_id])
    events = relationship("Event", back_populates="contract", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Contract(id={self.id}, client_id={self.client_id}, signed={self.is_signed})>"

    @property
    def is_fully_paid(self) -> bool:
        return self.remaining_amount <= 0

    @property
    def paid_amount(self) -> Decimal:
        return self.total_amount - self.remaining_amount

    @property
    def payment_percentage(self) -> float:
        if self.total_amount == 0:
            return 0.0
        return float((self.paid_amount / self.total_amount) * 100)

    @property
    def can_create_event(self) -> bool:
        return self.is_signed and not self.events
