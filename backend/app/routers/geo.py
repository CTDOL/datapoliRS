from typing import Dict, Any
from fastapi import APIRouter, Depends, Response
import asyncpg
from app.core.dependencies import getDbConnection
from app.services.geo_service import GeoService
from app.core.rate_limit import RateLimiter

router = APIRouter(
    prefix="/api/v1/geo",
    tags=["Geoespacial"],
    dependencies=[Depends(RateLimiter(times=30, seconds=1, configKey="geo"))]
)

# Limites municipais não mudam — o cache Redis destas rotas já usa TTL de 7 dias
# pelo mesmo motivo (GEOJSON_CACHE_TTL). Faltava dizer isso ao navegador e à
# Cloudflare: sem Cache-Control a resposta era tratada como dinâmica
# (cf-cache-status: DYNAMIC) e os ~520 KB comprimidos do GeoJSON eram baixados
# de novo a cada carregamento do Mapa Tático — que é a página inicial, e pesa
# em rede móvel.
#
# Um dia fresco, mais uma semana podendo servir a cópia velha enquanto
# revalida em segundo plano. O limite externo acompanha o TTL do Redis, então
# uma reimportação via etl/import_municipios_geojson.py leva no máximo um dia
# para aparecer — aceitável para divisas municipais.
GEO_CACHE_CONTROL = "public, max-age=86400, stale-while-revalidate=604800"


@router.get(
    "/municipios",
    summary="Recupera o GeoJSON dos municípios do RS",
    description="Retorna a FeatureCollection completa dos 496 municípios do Rio Grande do Sul gerada diretamente via PostGIS (ST_AsGeoJSON) com cache Redis."
)
async def obter_municipios_geojson(
    response: Response,
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> Dict[str, Any]:
    """Endpoint que serve as geometrias vetoriais dos municípios do RS com alta performance."""
    response.headers["Cache-Control"] = GEO_CACHE_CONTROL
    return await GeoService.getMunicipiosGeoJson(connection)

@router.get("/municipios/lista", summary="Lista leve de municípios com centróide")
async def obter_lista_municipios(
    response: Response,
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    response.headers["Cache-Control"] = GEO_CACHE_CONTROL
    return await GeoService.getMunicipiosList(connection)
