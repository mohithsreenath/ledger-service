from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    reference: Optional[str] = None


class TransactionCreate(TransactionBase):
    account_id: UUID
    type: TransactionType
    # For transfers, we'll need a receiver_id, but we can handle that in a specific schema or optional field
    receiver_id: Optional[UUID] = None


class TransactionResponse(BaseModel):
    id: UUID
    idempotency_key: Optional[str]
    type: TransactionType
    status: TransactionStatus
    reference: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
