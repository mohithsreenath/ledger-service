from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AccountBase(BaseModel):
    name: str
    currency: str


class AccountCreate(AccountBase):
    pass


class Account(AccountBase):
    id: UUID
    balance: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
