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
    employee_number = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    department = Column(Enum(Department), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations ORM
    clients = relationship("Client", back_populates="commercial_contact")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, " \
               f"department={self.department.value})>"

    @property
    def is_commercial(self) -> bool:
        return self.department == Department.COMMERCIAL

    @property
    def is_support(self) -> bool:
        return self.department == Department.SUPPORT

    @property
    def is_gestion(self) -> bool:
        return self.department == Department.GESTION
