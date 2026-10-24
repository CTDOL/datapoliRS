from typing import List
import os

from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from app.core.dependencies import getDbConnection, require_role
from app.core.rate_limit import RateLimiter
from app.schemas.user import UserInDB
from app.schemas.apis import ApiFonteResponse, ApisResponse, ApisUpdateRequest, MaxMindStatus
from app.schemas.system_config import ConfiguracaoItem, ConfiguracoesUpdateRequest
from app.services.apis_service import FONTES, ApisService
from app.services.system_config_service import SystemConfigService
from app.core.config import settings

NOMES_FONTES = {"tse": "TSE (DivulgaCandContas)", "camara": "Câmara dos Deputados", "senado": "Senado Federal", "alrs": "Assembleia Legislativa do RS"}

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Administração da Plataforma"],
    dependencies=[Depends(RateLimiter(times=10, seconds=1))]
)


@router.get(
    "/configuracoes",
    response_model=List[ConfiguracaoItem],
    summary="Lista as configurações globais da instância (ciclo eleitoral, rate limiting, cache)"
)
async def listar_configuracoes(
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> List[ConfiguracaoItem]:
    """Configurações globais da instância — afetam todos os gabinetes, não só o
    do usuário autenticado. Requer papel admin."""
    return await SystemConfigService.listAll(connection)


@router.put(
    "/configuracoes",
    response_model=List[ConfiguracaoItem],
    summary="Atualiza configurações globais da instância em runtime"
)
async def atualizar_configuracoes(
    payload: ConfiguracoesUpdateRequest,
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> List[ConfiguracaoItem]:
    """Aplica imediatamente (sem reiniciar o processo) — o cache de configuração
    é invalidado a cada gravação. Os endereços das APIs têm tela própria (/admin/apis),
    com validação de https."""
    if any(chave.startswith("api.") for chave in payload.valores):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endereços e liga/desliga das APIs são alterados na tela de APIs.",
        )
    return await SystemConfigService.updateMany(connection, payload.valores)


@router.get(
    "/apis",
    response_model=ApisResponse,
    summary="Endereços e situação das APIs externas usadas pelo sistema"
)
async def listar_apis(
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> ApisResponse:
    fontes = []
    for fonte, padrao in FONTES.items():
        fontes.append(ApiFonteResponse(
            fonte=fonte,
            nome=NOMES_FONTES[fonte],
            base_url=await ApisService.endereco(connection, fonte),
            ativa=await ApisService.ativa(connection, fonte),
            padrao=padrao,
        ))
    base_encontrada = bool(settings.GEOIP_DB_PATH) and os.path.exists(settings.GEOIP_DB_PATH)
    return ApisResponse(
        fontes=fontes,
        maxmind=MaxMindStatus(
            base_local_encontrada=base_encontrada,
            observacao="A chave MaxMind fica no .env do servidor e não é exibida nem alterada aqui.",
        ),
    )


@router.put(
    "/apis",
    response_model=ApisResponse,
    summary="Altera endereço e liga/desliga das APIs externas (somente https)"
)
async def atualizar_apis(
    payload: ApisUpdateRequest,
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> ApisResponse:
    atualizacoes = {}
    for item in payload.fontes:
        endereco = ApisService.enderecoValido(item.base_url)
        if endereco is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Endereço inválido para {NOMES_FONTES[item.fonte]}: use https:// e um endereço sem espaços.",
            )
        atualizacoes[f"api.{item.fonte}.base_url"] = endereco
        atualizacoes[f"api.{item.fonte}.ativa"] = "1" if item.ativa else "0"
    await SystemConfigService.updateMany(connection, atualizacoes)
    return await listar_apis(current_user, connection)
