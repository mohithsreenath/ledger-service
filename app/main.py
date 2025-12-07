from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings

from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command

import asyncio

# Automate migrations on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Alembic Upgrades
    try:
        alembic_cfg = Config("alembic.ini")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, command.upgrade, alembic_cfg, "head")
    except Exception as e:
        print(f"Migration failed: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME, 
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {"status": "ok"}
