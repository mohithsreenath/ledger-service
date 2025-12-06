import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(
        Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False
    )
    reference = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
