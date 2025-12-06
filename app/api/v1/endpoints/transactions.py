from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AccountNotFoundException, InsufficientFundsException
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.ledger import LedgerService

router = APIRouter()


@router.post(
    "/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    transaction_in: TransactionCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    service = LedgerService(db)
    try:
        return await service.process_transaction(transaction_in, idempotency_key)
    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientFundsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # In a real app, log this
        raise HTTPException(status_code=500, detail=str(e))
