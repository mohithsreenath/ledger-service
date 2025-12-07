from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.exceptions import AccountNotFoundException, InsufficientFundsException
from app.models.account import Account
from app.models.ledger_entry import EntryDirection, LedgerEntry
from app.models.transaction import Transaction, TransactionStatus, TransactionType
from app.schemas.account import AccountCreate
from app.schemas.transaction import TransactionCreate


class LedgerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_account(self, account_in: AccountCreate) -> Account:
        account = Account(name=account_in.name, currency=account_in.currency)
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def get_account(self, account_id: UUID) -> Account:
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise AccountNotFoundException(f"Account {account_id} not found")
        return account

    async def process_transaction(
        self, tx_in: TransactionCreate, idempotency_key: str = None
    ) -> Transaction:
        # 1. Check Idempotency
        if idempotency_key:
            stmt = select(Transaction).where(
                Transaction.idempotency_key == idempotency_key
            )
            result = await self.db.execute(stmt)
            existing_tx = result.scalar_one_or_none()
            if existing_tx:
                # Do NOT raise error. This allows clients to safely retry (e.g., on network timeout)
                # without duplicate billing or confusion.
                return existing_tx


        # 2. Lock Accounts (Pessimistic Locking)
        # Determine involved accounts
        involved_account_ids = [tx_in.account_id]
        if tx_in.type == TransactionType.TRANSFER and tx_in.receiver_id:
            involved_account_ids.append(tx_in.receiver_id)

        # Sort to prevent deadlocks
        involved_account_ids.sort()

        # Select FOR UPDATE
        # We fetch accounts in a loop or single query. Single query is better.
        stmt = (
            select(Account)
            .where(Account.id.in_(involved_account_ids))
            .with_for_update()
        )
        # Optional: Set a lock timeout here if needed for DoS protection
        # await self.db.execute(text("SET LOCAL lock_timeout = '4s'"))
        
        result = await self.db.execute(stmt)
        accounts_map = {acc.id: acc for acc in result.scalars().all()}

        # Validate all accounts exist
        if tx_in.account_id not in accounts_map:
            raise AccountNotFoundException(f"Account {tx_in.account_id} not found")
        if (
            tx_in.type == TransactionType.TRANSFER
            and tx_in.receiver_id
            and tx_in.receiver_id not in accounts_map
        ):
            raise AccountNotFoundException(
                f"Receiver account {tx_in.receiver_id} not found"
            )

        account = accounts_map[tx_in.account_id]

        # 3. Validation & Balance Update
        if tx_in.type == TransactionType.DEPOSIT:
            account.balance += tx_in.amount
        elif tx_in.type == TransactionType.WITHDRAWAL:
            if account.balance < tx_in.amount:
                raise InsufficientFundsException(
                    f"Insufficient funds for withdrawal. Balance: {account.balance}"
                )
            account.balance -= tx_in.amount
        elif tx_in.type == TransactionType.TRANSFER:
            receiver = accounts_map[tx_in.receiver_id]
            if account.balance < tx_in.amount:
                raise InsufficientFundsException(
                    f"Insufficient funds for transfer. Balance: {account.balance}"
                )
            account.balance -= tx_in.amount
            receiver.balance += tx_in.amount

        # 4. Create Transaction Record
        transaction = Transaction(
            idempotency_key=idempotency_key,
            type=tx_in.type,
            status=TransactionStatus.COMPLETED,
            reference=tx_in.reference,
        )
        self.db.add(transaction)
        await self.db.flush()  # Get ID

        # 5. Create Ledger Entries (Double Entry)
        entries = []
        if tx_in.type == TransactionType.DEPOSIT:
            # Credit User
            entries.append(
                LedgerEntry(
                    transaction_id=transaction.id,
                    account_id=account.id,
                    amount=tx_in.amount,
                    direction=EntryDirection.CREDIT,
                )
            )
            # Debit System (Implicit/Virtual for now, or we'd add a system account entry)

        elif tx_in.type == TransactionType.WITHDRAWAL:
            # Debit User
            entries.append(
                LedgerEntry(
                    transaction_id=transaction.id,
                    account_id=account.id,
                    amount=-tx_in.amount,
                    direction=EntryDirection.DEBIT,
                )
            )

        elif tx_in.type == TransactionType.TRANSFER:
            # Debit Sender
            entries.append(
                LedgerEntry(
                    transaction_id=transaction.id,
                    account_id=account.id,
                    amount=-tx_in.amount,
                    direction=EntryDirection.DEBIT,
                )
            )
            # Credit Receiver
            entries.append(
                LedgerEntry(
                    transaction_id=transaction.id,
                    account_id=receiver.id,
                    amount=tx_in.amount,
                    direction=EntryDirection.CREDIT,
                )
            )

        self.db.add_all(entries)

        # 6. Commit
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def get_account_history(
        self, account_id: UUID, limit: int = 100, offset: int = 0
    ):
        stmt = (
            select(LedgerEntry)
            .where(LedgerEntry.account_id == account_id)
            .order_by(LedgerEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
