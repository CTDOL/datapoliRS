from typing import List

import asyncpg
from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import getDbConnection, require_role
from app.core.rate_limit import RateLimiter
from app.repositories.manutencao_repository import ManutencaoRepository
from app.schemas.manutencao import AtivarPleitoRequest, CargaEtl, JobEtl, JobEtlCreate, PleitoAtivo, SaudePleito
from app.schemas.user import UserInDB
from app.services.manutencao_service import ManutencaoService


def get_manutencao_service() -> ManutencaoService:
    return ManutencaoService(manutencao_repo=ManutencaoRepository())


router = APIRouter(
    prefix="/api/v1/admin/manutencao",
    tags=["Manutenção de Dados Eleitorais"],
    dependencies=[Depends(RateLimiter(times=10, seconds=1))]
)


@router.get(
    "/saude",
    response_model=List[SaudePleito],
    summary="Saúde dos dados por pleito carregado (votação e comparecimento)"
)
async def saude_por_pleito(
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
    servico: ManutencaoService = Depends(get_manutencao_service),
) -> List[SaudePleito]:
    """Dados globais da instância. Requer papel admin."""
    return await servico.saude_por_pleito(connection)


@router.get(
    "/cargas",
    response_model=List[CargaEtl],
    summary="Histórico de cargas do ETL eleitoral, mais recente primeiro"
)
async def listar_cargas(
    limite: int = Query(50, ge=1, le=500),
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
    servico: ManutencaoService = Depends(get_manutencao_service),
) -> List[CargaEtl]:
    """Requer papel admin."""
    return await servico.listar_cargas(connection, limite)


@router.get(
    "/jobs",
    response_model=List[JobEtl],
    summary="Fila de cargas do ETL (pendentes, em execução e concluídas)"
)
async def listar_jobs(
    limite: int = Query(20, ge=1, le=200),
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
    servico: ManutencaoService = Depends(get_manutencao_service),
) -> List[JobEtl]:
    return await servico.listar_jobs(connection, limite)


@router.post(
    "/jobs",
    response_model=JobEtl,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enfileira a carga de um pleito para o worker de ETL"
)
async def enfileirar_carga(
    payload: JobEtlCreate,
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
    servico: ManutencaoService = Depends(get_manutencao_service),
) -> JobEtl:
    """Exige a confirmação exata 'CARREGAR <TIPO> <ANO>' (ex.: CARREGAR VOTACAO 2026).
    Só um job ativo por vez: com outro em andamento, responde 409."""
    return await servico.enfileirar_carga(connection, payload, current_user.email)


@router.post(
    "/ativar-pleito",
    response_model=PleitoAtivo,
    summary="Torna um pleito carregado o ativo da plataforma, com checagem e auditoria"
)
async def ativar_pleito(
    payload: AtivarPleitoRequest,
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
    servico: ManutencaoService = Depends(get_manutencao_service),
) -> PleitoAtivo:
    """Gates, nesta ordem:
    1. o pleito existe em tb_eleicoes (404);
    2. existe carga de votação concluída com sucesso para ele (409);
    3. se houver códigos de município sem cadastro, exige aceitação explícita (409);
    4. a confirmação deve ser exatamente 'ATIVAR <ANO>' (400).
    Grava o novo pleito em tb_configuracoes_sistema e registra a troca em tb_auditoria_manutencao."""
    return await servico.ativar_pleito(connection, payload, current_user.email)
