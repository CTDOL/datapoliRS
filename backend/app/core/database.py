import logging
from typing import Optional, AsyncGenerator
import asyncpg
from app.core.config import settings

logger = logging.getLogger("DatabasePool")

databasePool: Optional[asyncpg.Pool] = None


import asyncio

async def initializeDatabasePool() -> asyncpg.Pool:
    """Inicializa o pool de conexões assíncronas com o PostgreSQL/PostGIS."""
    global databasePool
    try:
        currentLoop = asyncio.get_running_loop()
    except RuntimeError:
        currentLoop = None

    isPoolStale = (
        databasePool is None
        or databasePool._closed
        or (currentLoop is not None and databasePool._loop != currentLoop)
    )

    if isPoolStale:
        logger.info(f"Conectando ao PostgreSQL via asyncpg (DATABASE_URL={settings.DATABASE_URL})...")
        try:
            if settings.DATABASE_URL:
                databasePool = await asyncpg.create_pool(
                    dsn=settings.DATABASE_URL,
                    min_size=2,
                    max_size=20,
                    command_timeout=30.0
                )
            else:
                databasePool = await asyncpg.create_pool(
                    user=settings.POSTGRES_USER,
                    password=settings.POSTGRES_PASSWORD,
                    database=settings.POSTGRES_DB,
                    host=settings.POSTGRES_HOST,
                    port=settings.POSTGRES_PORT,
                    min_size=2,
                    max_size=20,
                    command_timeout=30.0
                )
            logger.info("Pool de conexões PostgreSQL/PostGIS criado com sucesso.")
        except Exception as databaseError:
            logger.error(f"FALHA CRÍTICA: Erro ao inicializar pool asyncpg: {databaseError}", exc_info=True)
            raise RuntimeError(f"Database pool initialization error: {databaseError}") from databaseError
    return databasePool


async def closeDatabasePool() -> None:
    """Encerra o pool de conexões com o PostgreSQL."""
    global databasePool
    if databasePool is not None:
        logger.info("Fechando pool de conexões PostgreSQL...")
        await databasePool.close()
        databasePool = None
        logger.info("Pool PostgreSQL encerrado.")


async def getDatabaseConnection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Dependency para obter uma conexão ativa do pool assíncrono."""
    global databasePool
    if databasePool is None:
        await initializeDatabasePool()
    
    async with databasePool.acquire() as connection:
        yield connection
