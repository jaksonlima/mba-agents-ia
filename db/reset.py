import asyncio
from db.engine import Base, close_db, engine

async def reset_db() -> None:
    """Apaga todas as tabelas do banco de dados e as recria (idempotente)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await close_db()


if __name__ == "__main__":
    asyncio.run(reset_db())