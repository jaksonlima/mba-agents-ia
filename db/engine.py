import os
from pathlib import Path
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from db.models import Base

# Caminho base relativo ao arquivo atual
BASE_PATH = Path(__file__).resolve().parent.parent / "agents"

# Garante que o diretório de destino exista caso seja usado SQLite
BASE_PATH.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BASE_PATH}/tickets.db",
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


async def init_db() -> None:
    """Cria as tabelas se não existirem (idempotente)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Fecha o pool de conexões chamado no shutdown."""
    await engine.dispose()