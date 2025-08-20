from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    commercial_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    commercial_contact = relationship("User", back_populates="clients",
                                      foreign_keys=[commercial_contact_id])
    contracts = relationship("Contract", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.full_name}, company={self.company_name})>"

    @property
    def has_signed_contracts(self) -> bool:
        return any(contract.is_signed for contract in self.contracts)

    @property
    def total_contract_amount(self) -> float:
        return sum(float(contract.total_amount) for contract in self.contracts if contract.is_signed)
