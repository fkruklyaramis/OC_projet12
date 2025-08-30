from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base
from src.utils.hash_utils import hash_password, verify_password
import enum


class Department(enum.Enum):
    COMMERCIAL = "commercial"
    SUPPORT = "support"
    GESTION = "gestion"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    employee_number = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    department = Column(Enum(Department), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations ORM
    clients = relationship("Client", back_populates="commercial_contact")

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, " \
               f"department={self.department.value})>"

    def set_password(self, password: str):
        """Hasher et définir le mot de passe avec Argon2"""
        self.hashed_password = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Vérifier le mot de passe avec Argon2"""
        return verify_password(self.hashed_password, password)

    @property
    def is_commercial(self) -> bool:
        return self.department == Department.COMMERCIAL

    @property
    def is_support(self) -> bool:
        return self.department == Department.SUPPORT

    @property
    def is_gestion(self) -> bool:
        return self.department == Department.GESTION
