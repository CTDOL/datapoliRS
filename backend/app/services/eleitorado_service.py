import logging
from typing import List, Dict, Any, Optional
import asyncpg
from app.core.redis_client import CacheService
from app.repositories.eleitorado_repository import EleitoradoRepository
from app.services.system_config_service import SystemConfigService

logger = logging.getLogger("EleitoradoService")

CACHE_TTL_DEFAULT = 86400  # 1 dia — eleitorado/comparecimento de um pleito já apurado é imutável


class EleitoradoService:
    """Serviço de eleitorado apto e comparecimento real, com cache Redis por ano."""

    @staticmethod
    async def getComparecimentoByMunicipio(connection: asyncpg.Connection, ano: int) -> List[Dict[str, Any]]:
        cacheKey = f"eleitorado:rs:municipios:{ano}"
        cachedData = await CacheService.get(cacheKey)
        if cachedData is not None:
            return cachedData

        data = await EleitoradoRepository.getComparecimentoByMunicipio(connection, ano)
        if data:
            ttl = await SystemConfigService.getInt(connection, "cache_ttl.eleitorado", CACHE_TTL_DEFAULT)
            await CacheService.set(cacheKey, data, ttlSeconds=ttl)
        return data

    @staticmethod
    async def getTotalRs(connection: asyncpg.Connection, ano: int) -> Optional[Dict[str, Any]]:
        cacheKey = f"eleitorado:rs:total:{ano}"
        cachedData = await CacheService.get(cacheKey)
        if cachedData is not None:
            return cachedData

        data = await EleitoradoRepository.getTotalRs(connection, ano)
        if data:
            ttl = await SystemConfigService.getInt(connection, "cache_ttl.eleitorado", CACHE_TTL_DEFAULT)
            await CacheService.set(cacheKey, data, ttlSeconds=ttl)
        return data
