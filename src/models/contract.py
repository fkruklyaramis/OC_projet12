from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base
import enum


class ContractStatus(enum.Enum):
    DRAFT = "draft"
    SIGNED = "signed" 
    CANCELLED = "cancelled"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    amount_due = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT, nullable=False)
    signed = Column(Boolean, default=False, nullable=False)
    
    # Relations
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    commercial_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    signed_at = Column(DateTime(timezone=True), nullable=True)

    # Relations ORM
    client = relationship("Client", back_populates="contracts")
    commercial_contact = relationship("User", foreign_keys=[commercial_contact_id])
    events = relationship("Event", back_populates="contract")

    def __repr__(self):
        return f"<Contract(id={self.id}, client_id={self.client_id}, " \
               f"amount={self.total_amount}, status={self.status.value})>"

    @property
    def is_signed(self) -> bool:
        return self.signed and self.status == ContractStatus.SIGNED

    @property
    def is_fully_paid(self) -> bool:
        return self.amount_due <= 0

    @property
    def remaining_amount(self) -> float:
        return float(self.amount_due)