import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
import asyncpg
from app.core.dependencies import getDbConnection, get_current_user, require_role
from app.schemas.user import UserInDB
from app.services.amendment_service import AmendmentService
from app.schemas.budget_amendment import (
    EmendaCreate,
    EmendaUpdate,
    EmendaResponse,
    EmendaPageResponse,
    EmendaKpis,
)
from app.core.rate_limit import RateLimiter

router = APIRouter(
    prefix="/api/v1/gabinete/emendas",
    tags=["Gabinete Digital & Emendas Orçamentárias"],
    dependencies=[Depends(RateLimiter(times=30, seconds=1))]
)


@router.post(
    "",
    response_model=EmendaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma nova emenda orçamentária no gabinete"
)
async def cadastrar_emenda(
    payload: EmendaCreate,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> EmendaResponse:
    """Cria uma nova emenda vinculada exclusivamente ao gabinete (tenant_id)."""
    return await AmendmentService.createAmendment(connection, current_user.tenant_id, payload)


@router.get(
    "/kpis",
    response_model=EmendaKpis,
    summary="Indicadores agregados das emendas do gabinete (totais e por situação)"
)
async def obter_kpis_emendas(
    ano_exercicio: Optional[int] = Query(None, description="Filtrar KPIs por ano de exercício"),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> EmendaKpis:
    """Retorna totais indicado/empenhado/pago e contagem por situação, isolados por gabinete."""
    return await AmendmentService.getKpis(connection, current_user.tenant_id, ano_exercicio)


@router.get(
    "",
    response_model=EmendaPageResponse,
    summary="Lista as emendas orçamentárias do gabinete, paginadas, com filtros"
)
async def listar_emendas(
    cd_ibge_7: Optional[str] = Query(None, description="Filtrar por código IBGE do município beneficiário"),
    ano_exercicio: Optional[int] = Query(None, description="Filtrar por ano de exercício"),
    tp_situacao: Optional[str] = Query(None, description="Filtrar por situação (Indicada, Empenhada, Paga, Cancelada)"),
    termo: Optional[str] = Query(None, description="Busca por objeto/número da emenda"),
    page: int = Query(1, ge=1, description="Número da página (1-indexado)"),
    page_size: int = Query(50, ge=1, le=200, description="Quantidade de registros por página"),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> EmendaPageResponse:
    """Recupera a lista paginada de emendas cadastradas no gabinete isolado."""
    return await AmendmentService.listAmendments(
        connection=connection,
        tenantId=current_user.tenant_id,
        ibgeCode=cd_ibge_7,
        anoExercicio=ano_exercicio,
        tpSituacao=tp_situacao,
        searchTerm=termo,
        page=page,
        pageSize=page_size
    )


@router.get(
    "/{id_emenda}",
    response_model=EmendaResponse,
    summary="Recupera detalhes de uma emenda pelo ID"
)
async def obter_emenda_por_id(
    id_emenda: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> EmendaResponse:
    """Retorna os dados da emenda se pertencer ao gabinete autenticado."""
    return await AmendmentService.getAmendmentById(connection, current_user.tenant_id, id_emenda)


@router.put(
    "/{id_emenda}",
    response_model=EmendaResponse,
    summary="Atualiza dados de uma emenda orçamentária"
)
async def atualizar_emenda(
    id_emenda: uuid.UUID,
    payload: EmendaUpdate,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> EmendaResponse:
    """Atualiza as informações da emenda no gabinete."""
    return await AmendmentService.updateAmendment(connection, current_user.tenant_id, id_emenda, payload)


@router.delete(
    "/{id_emenda}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma emenda orçamentária do gabinete (requer papel admin)"
)
async def remover_emenda(
    id_emenda: uuid.UUID,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> None:
    """Exclui a emenda do gabinete garantindo isolamento por tenant_id."""
    await AmendmentService.deleteAmendment(connection, current_user.tenant_id, id_emenda)
