import logging
from typing import Dict, List, Any, Optional
from fastapi import HTTPException, status
import asyncpg
from app.core.redis_client import CacheService
from app.repositories.system_config_repository import SystemConfigRepository

logger = logging.getLogger("SystemConfigService")

CONFIG_CACHE_KEY = "system:config:all"
CONFIG_CACHE_TTL = 60  # segundos — janela curta para uma edição na tela propagar rápido


class SystemConfigService:
    """Configurações globais da instância (ciclo eleitoral, rate limiting, TTL de
    cache), editáveis em runtime via tela de administração — sem reiniciar o
    processo nem editar .env. Cache Redis curto equilibra performance (evita ir
    ao Postgres a cada request) com velocidade de propagação de uma edição."""

    @staticmethod
    async def _loadMap(connection: asyncpg.Connection) -> Dict[str, str]:
        cached = await CacheService.get(CONFIG_CACHE_KEY)
        if cached is not None:
            return cached
        rows = await SystemConfigRepository.getAll(connection)
        configMap = {row["chave"]: row["valor"] for row in rows}
        await CacheService.set(CONFIG_CACHE_KEY, configMap, ttlSeconds=CONFIG_CACHE_TTL)
        return configMap

    @staticmethod
    async def getInt(connection: asyncpg.Connection, chave: str, default: int) -> int:
        configMap = await SystemConfigService._loadMap(connection)
        valor = configMap.get(chave)
        try:
            return int(valor) if valor is not None else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    async def getStr(connection: asyncpg.Connection, chave: str, default: str) -> str:
        configMap = await SystemConfigService._loadMap(connection)
        return configMap.get(chave) or default

    @staticmethod
    async def getIntFromCacheOnly(chave: str, default: int) -> int:
        """Leitura só-Redis, sem conexão de banco — usada em caminhos de alta
        frequência (ex: RateLimiter) onde abrir uma conexão do pool só para isso
        não compensa. Se o cache ainda não foi aquecido, usa o default do
        chamador; o cache é aquecido no startup e a cada leitura via _loadMap."""
        cached: Optional[Dict[str, Any]] = await CacheService.get(CONFIG_CACHE_KEY)
        if cached is None:
            return default
        valor = cached.get(chave)
        try:
            return int(valor) if valor is not None else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    async def listAll(connection: asyncpg.Connection) -> List[Dict[str, Any]]:
        return await SystemConfigRepository.getAll(connection)

    @staticmethod
    async def updateMany(connection: asyncpg.Connection, updates: Dict[str, str]) -> List[Dict[str, Any]]:
        existingRows = await SystemConfigRepository.getAll(connection)
        existingByKey = {row["chave"]: row for row in existingRows}

        unknownKeys = [chave for chave in updates if chave not in existingByKey]
        if unknownKeys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chave(s) de configuração desconhecida(s): {', '.join(unknownKeys)}"
            )

        for chave, valor in updates.items():
            if existingByKey[chave]["tipo"] == "int":
                try:
                    int(valor)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Valor inválido para '{chave}': esperado um número inteiro."
                    )

        await SystemConfigRepository.updateMany(connection, updates)
        await CacheService.delete(CONFIG_CACHE_KEY)
        logger.info(f"Configurações do sistema atualizadas: {list(updates.keys())}")
        return await SystemConfigRepository.getAll(connection)

    @staticmethod
    async def warmCache(connection: asyncpg.Connection) -> None:
        """Aquece o cache no startup da aplicação, para o RateLimiter (que só lê
        do Redis) já enxergar valores atualizados desde a primeira requisição."""
        await CacheService.delete(CONFIG_CACHE_KEY)
        await SystemConfigService._loadMap(connection)
