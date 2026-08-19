from typing import Dict, Any
from fastapi import APIRouter, Depends
import asyncpg
from app.core.dependencies import getDbConnection
from app.services.geo_service import GeoService

router = APIRouter(prefix="/api/v1/geo", tags=["Geoespacial"])


@router.get(
    "/municipios",
    summary="Recupera o GeoJSON dos municípios do RS",
    description="Retorna a FeatureCollection completa dos 496 municípios do Rio Grande do Sul gerada diretamente via PostGIS (ST_AsGeoJSON) com cache Redis."
)
async def obter_municipios_geojson(
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> Dict[str, Any]:
    """Endpoint que serve as geometrias vetoriais dos municípios do RS com alta performance."""
    return await GeoService.getMunicipiosGeoJson(connection)
