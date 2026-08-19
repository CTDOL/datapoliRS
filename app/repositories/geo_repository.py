import json
import logging
from typing import Dict, Any
import asyncpg

logger = logging.getLogger("GeoRepository")


class GeoRepository:
    """Repositório de dados geoespaciais com processamento nativo via PostGIS."""

    @staticmethod
    async def getMunicipiosFeatureCollection(connection: asyncpg.Connection) -> Dict[str, Any]:
        """Gera o GeoJSON FeatureCollection completo diretamente no motor PostGIS."""
        query = """
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'properties', json_build_object(
                            'id', m.cd_ibge_7,
                            'name', m.nm_municipio,
                            'cd_tse', m.cd_tse,
                            'description', m.nm_municipio
                        ),
                        'geometry', ST_AsGeoJSON(m.geometria)::json
                    ) ORDER BY m.nm_municipio
                ), '[]'::json)
            ) AS geojson
            FROM tb_municipios m
            WHERE m.geometria IS NOT NULL;
        """
        try:
            row = await connection.fetchrow(query)
            if not row or not row["geojson"]:
                logger.warning("Nenhum dado geográfico retornado pelo PostGIS.")
                return {"type": "FeatureCollection", "features": []}
            
            rawResult = row["geojson"]
            if isinstance(rawResult, str):
                return json.loads(rawResult)
            return rawResult

        except asyncpg.PostgresError as postgresError:
            logger.error(f"Erro ao executar agregação espacial ST_AsGeoJSON: {postgresError}", exc_info=True)
            raise RuntimeError(f"Database spatial query failure: {postgresError}") from postgresError
