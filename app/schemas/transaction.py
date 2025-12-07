from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic import model_validator


class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TransactionBase(BaseModel):
    # We accept strings or numbers for Decimal to ensure precision
    # strict=False allow "100.00" string input which is standard safe practice
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    reference: Optional[str] = None


class TransactionCreate(TransactionBase):
    account_id: UUID
    type: TransactionType
    receiver_id: Optional[UUID] = None

    @model_validator(mode='after')
    def validate_transaction_logic(self) -> 'TransactionCreate':
        # 1. TRANSFER requires receiver_id
        if self.type == TransactionType.TRANSFER and not self.receiver_id:
            raise ValueError("Receiver account ID is required for transfers.")
        
        # 2. DEPOSIT/WITHDRAWAL should NOT have receiver_id
        if self.type in [TransactionType.DEPOSIT, TransactionType.WITHDRAWAL] and self.receiver_id:
            raise ValueError(f"Receiver account ID must not be provided for {self.type.value}.")
            
        # 3. Cannot transfer to self
        if self.type == TransactionType.TRANSFER and self.account_id == self.receiver_id:
            raise ValueError("Cannot transfer funds to the same account.")
            
        return self


class TransactionResponse(BaseModel):
    id: UUID
    idempotency_key: Optional[str]
    type: TransactionType
    status: TransactionStatus
    reference: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
