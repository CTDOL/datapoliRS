from typing import List
from fastapi import APIRouter, Depends
import asyncpg
from app.core.dependencies import getDbConnection, require_role
from app.core.rate_limit import RateLimiter
from app.schemas.user import UserInDB
from app.schemas.system_config import ConfiguracaoItem, ConfiguracoesUpdateRequest
from app.services.system_config_service import SystemConfigService

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
    current_user: UserInDB = Depends(require_role(["admin"])),
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
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> List[ConfiguracaoItem]:
    """Aplica imediatamente (sem reiniciar o processo) — o cache de configuração
    é invalidado a cada gravação."""
    return await SystemConfigService.updateMany(connection, payload.valores)
