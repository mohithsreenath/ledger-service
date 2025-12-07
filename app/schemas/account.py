from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class AccountBase(BaseModel):
    name: str
    currency: str = "USD"  # Defaults to USD, but we should validate or use Enum if strictness needed. 
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v.upper() not in ["USD", "INR"]:
             raise ValueError("Currency must be USD or INR")
        return v.upper()


class AccountCreate(AccountBase):
    pass


class Account(AccountBase):
    id: UUID
    balance: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
