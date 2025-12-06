import uuid

from sqlalchemy import Column, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    currency = Column(String(3), nullable=False)  # USD, INR
    balance = Column(Numeric(20, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
