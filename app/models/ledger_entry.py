import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class EntryDirection(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False
    )
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    amount = Column(
        Numeric(20, 2), nullable=False
    )  # Signed amount: + for Credit, - for Debit
    direction = Column(Enum(EntryDirection), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
