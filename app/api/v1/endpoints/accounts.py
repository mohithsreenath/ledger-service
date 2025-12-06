from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AccountNotFoundException
from app.schemas.account import Account, AccountCreate
from app.services.ledger import LedgerService

router = APIRouter()


@router.post("/", response_model=Account, status_code=status.HTTP_201_CREATED)
async def create_account(account_in: AccountCreate, db: AsyncSession = Depends(get_db)):
    service = LedgerService(db)
    return await service.create_account(account_in)


@router.get("/{account_id}", response_model=Account)
async def get_account(account_id: UUID, db: AsyncSession = Depends(get_db)):
    service = LedgerService(db)
    try:
        return await service.get_account(account_id)
    except AccountNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{account_id}/history")
async def get_account_history(
    account_id: UUID,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    service = LedgerService(db)
    return await service.get_account_history(account_id, limit, offset)
