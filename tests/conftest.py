import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Use NullPool to avoid asyncpg InterfaceError in tests
TEST_DATABASE_URL = settings.DATABASE_URL

# Redefine event_loop to be session scoped to work with session-scoped engine if needed
# But here we will keep engine function-scoped or module-scoped but ensure it's created inside the loop context if possible.
# Actually, the simplest fix for "attached to a different loop" with asyncpg is to use the same loop or recreate engine.


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine, class_=AsyncSession
    )
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def clear_db(db_session):
    # Clear tables before each test
    from sqlalchemy import delete

    from app.models.account import Account
    from app.models.ledger_entry import LedgerEntry
    from app.models.transaction import Transaction

    await db_session.execute(delete(LedgerEntry))
    await db_session.execute(delete(Transaction))
    await db_session.execute(delete(Account))
    await db_session.commit()
