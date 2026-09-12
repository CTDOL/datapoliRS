from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
import asyncpg
from app.core.config import settings
from app.core.dependencies import getDbConnection
from app.services.eleitorado_service import EleitoradoService
from app.services.system_config_service import SystemConfigService
from app.core.rate_limit import RateLimiter

router = APIRouter(
    prefix="/api/v1/eleitorado",
    tags=["Eleitorado & Comparecimento"],
    dependencies=[Depends(RateLimiter(times=30, seconds=1, configKey="eleitorado"))]
)


@router.get(
    "/municipios",
    response_model=List[Dict[str, Any]],
    summary="Eleitorado apto, comparecimento e abstenções por município"
)
async def listar_comparecimento_por_municipio(
    ano: Optional[int] = Query(None, description="Ano da eleição (padrão: configuração da plataforma)"),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> List[Dict[str, Any]]:
    """Retorna, para cada município do RS, quantos eleitores estavam aptos,
    quantos compareceram e quantos se abstiveram no pleito informado."""
    anoResolvido = ano if ano is not None else await SystemConfigService.getInt(connection, "eleitoral.election_year", settings.ELECTION_YEAR)
    return await EleitoradoService.getComparecimentoByMunicipio(connection, anoResolvido)


@router.get(
    "/total",
    response_model=Dict[str, Any],
    summary="Total de eleitorado apto e comparecimento no RS"
)
async def obter_total_eleitorado_rs(
    ano: Optional[int] = Query(None, description="Ano da eleição (padrão: configuração da plataforma)"),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> Dict[str, Any]:
    """Soma estadual de eleitorado apto, comparecimento e abstenções para o pleito informado."""
    anoResolvido = ano if ano is not None else await SystemConfigService.getInt(connection, "eleitoral.election_year", settings.ELECTION_YEAR)
    total = await EleitoradoService.getTotalRs(connection, anoResolvido)
    if total is None:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum dado de eleitorado/comparecimento carregado para o ano {anoResolvido}. "
                   f"Rode 'make etl-comparecimento ano={anoResolvido}' após baixar o arquivo do TSE."
        )
    return total
