import logging
from typing import Dict, Any
import asyncpg
from app.core.redis_client import CacheService
from app.repositories.geo_repository import GeoRepository

logger = logging.getLogger("GeoService")

GEOJSON_CACHE_KEY = "geo:rs:municipios:feature_collection"
GEOJSON_CACHE_TTL = 86400 * 7  # 7 Dias (geometrias são estáticas)


class GeoService:

    @staticmethod
    async def getMunicipiosList(connection: asyncpg.Connection) -> list:
        cachedData = await CacheService.get("geo:rs:municipios:lista")
        if cachedData:
            return cachedData
        data = await GeoRepository.getMunicipiosList(connection)
        if data:
            await CacheService.set("geo:rs:municipios:lista", data, ttlSeconds=GEOJSON_CACHE_TTL)
        return data

    """Serviço de inteligência geoespacial com cache Redis e processamento PostGIS."""

    @staticmethod
    async def getMunicipiosGeoJson(connection: asyncpg.Connection) -> Dict[str, Any]:
        """Recupera o GeoJSON dos municípios do RS com estratégia Cache-Aside."""
        # 1. Tentar ler do Cache Redis
        cachedData = await CacheService.get(GEOJSON_CACHE_KEY)
        if cachedData:
            logger.info("GeoJSON recuperado do Cache Redis.")
            return cachedData

        # 2. Em caso de Cache Miss ou Fallback, consultar PostGIS
        logger.info("Cache MISS: Gerando GeoJSON diretamente via PostGIS ST_AsGeoJSON...")
        geoJsonData = await GeoRepository.getMunicipiosFeatureCollection(connection)

        # 3. Gravar no Cache em background sem travar retorno
        if geoJsonData and geoJsonData.get("features"):
            await CacheService.set(GEOJSON_CACHE_KEY, geoJsonData, ttlSeconds=GEOJSON_CACHE_TTL)

        return geoJsonData
