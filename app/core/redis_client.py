import json
import logging
from typing import Optional, Any
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger("RedisClient")

redisClientInstance: Optional[aioredis.Redis] = None


async def initializeRedisClient() -> Optional[aioredis.Redis]:
    """Inicializa a conexão assíncrona com o Redis."""
    global redisClientInstance
    if redisClientInstance is None:
        try:
            logger.info(f"Conectando ao Redis em {settings.REDIS_HOST}:{settings.REDIS_PORT}...")
            redisClientInstance = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0
            )
            await redisClientInstance.ping()
            logger.info("Conexão com Redis estabelecida com sucesso.")
        except Exception as redisError:
            logger.warning(
                f"AVISO: Redis indisponível no startup ({redisError}). A API operará em modo Fallback (Postgres direto).",
                exc_info=True
            )
            redisClientInstance = None
    return redisClientInstance


async def closeRedisClient() -> None:
    """Encerra a conexão com o Redis."""
    global redisClientInstance
    if redisClientInstance is not None:
        logger.info("Fechando conexão com Redis...")
        await redisClientInstance.close()
        redisClientInstance = None
        logger.info("Conexão Redis encerrada.")


class CacheService:
    """Serviço de cache com fallback gracioso para garantir alta resiliência."""

    @staticmethod
    async def get(cacheKey: str) -> Optional[Any]:
        """Recupera valor do cache. Se o Redis falhar, retorna None sem travar a requisição."""
        global redisClientInstance
        if redisClientInstance is None:
            return None
        try:
            cachedValue = await redisClientInstance.get(cacheKey)
            if cachedValue:
                logger.debug(f"Cache HIT para chave: {cacheKey}")
                return json.loads(cachedValue)
            logger.debug(f"Cache MISS para chave: {cacheKey}")
            return None
        except Exception as cacheError:
            logger.warning(f"Falha de leitura no Redis para chave '{cacheKey}' ({cacheError}). Prosseguindo sem cache.")
            return None

    @staticmethod
    async def set(cacheKey: str, payload: Any, ttlSeconds: Optional[int] = None) -> bool:
        """Grava valor no cache com TTL. Se falhar, registra log e não bloqueia a execução."""
        global redisClientInstance
        if redisClientInstance is None:
            return False
        try:
            ttl = ttlSeconds if ttlSeconds is not None else settings.CACHE_DEFAULT_TTL
            serializedPayload = json.dumps(payload, ensure_ascii=False)
            await redisClientInstance.set(cacheKey, serializedPayload, ex=ttl)
            logger.debug(f"Cache SET gravado com sucesso: chave={cacheKey}, ttl={ttl}s")
            return True
        except Exception as cacheError:
            logger.warning(f"Falha de escrita no Redis para chave '{cacheKey}' ({cacheError}).")
            return False

    @staticmethod
    async def delete(cacheKey: str) -> bool:
        """Remove chave do cache."""
        global redisClientInstance
        if redisClientInstance is None:
            return False
        try:
            await redisClientInstance.delete(cacheKey)
            return True
        except Exception as cacheError:
            logger.warning(f"Falha ao deletar chave '{cacheKey}' no Redis ({cacheError}).")
            return False
