from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base
import enum


class Department(enum.Enum):
    COMMERCIAL = "commercial"
    SUPPORT = "support"
    GESTION = "gestion"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    department = Column(Enum(Department), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    clients = relationship("Client", back_populates="commercial_contact",
                           foreign_keys="Client.commercial_contact_id")
    contracts = relationship("Contract", back_populates="commercial_contact",
                             foreign_keys="Contract.commercial_contact_id")
    events = relationship("Event", back_populates="support_contact",
                          foreign_keys="Event.support_contact_id")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, department={self.department.value})>"

    @property
    def is_commercial(self) -> bool:
        return self.department == Department.COMMERCIAL

    @property
    def is_support(self) -> bool:
        return self.department == Department.SUPPORT

    @property
    def is_gestion(self) -> bool:
        return self.department == Department.GESTION
