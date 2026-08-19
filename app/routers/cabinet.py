import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
import asyncpg
from app.core.dependencies import getDbConnection, get_current_user
from app.schemas.user import UserInDB
from app.services.cabinet_service import CabinetService
from app.schemas.leadership import (
    LiderancaCreate,
    LiderancaUpdate,
    LiderancaResponse
)

router = APIRouter(prefix="/api/v1/gabinete/liderancas", tags=["Gabinete Digital & Lideranças"])


@router.post(
    "",
    response_model=LiderancaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma nova liderança política no gabinete"
)
async def cadastrar_lideranca(
    payload: LiderancaCreate,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> LiderancaResponse:
    """Cria uma nova liderança vinculada exclusivamente ao gabinete (tenant_id)."""
    return await CabinetService.createLeadership(connection, current_user.tenant_id, payload)


@router.get(
    "",
    response_model=List[LiderancaResponse],
    summary="Lista todas as lideranças do gabinete com filtros"
)
async def listar_liderancas(
    cd_ibge_7: Optional[str] = Query(None, description="Filtrar por código IBGE do município"),
    tp_influencia: Optional[str] = Query(None, description="Filtrar por categoria de influência"),
    is_ativo: Optional[bool] = Query(None, description="Filtrar por status ativo/inativo"),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> List[LiderancaResponse]:
    """Recupera a lista de lideranças cadastradas no gabinete isolado."""
    return await CabinetService.listLeaderships(
        connection=connection,
        tenantId=current_user.tenant_id,
        ibgeCode=cd_ibge_7,
        influenceCategory=tp_influencia,
        isActive=is_ativo
    )


@router.get(
    "/{id_lideranca}",
    response_model=LiderancaResponse,
    summary="Recupera detalhes de uma liderança pelo ID"
)
async def obter_lideranca_por_id(
    id_lideranca: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> LiderancaResponse:
    """Retorna os dados cadastrais da liderança se pertencer ao gabinete autenticado."""
    return await CabinetService.getLeadershipById(connection, current_user.tenant_id, id_lideranca)


@router.put(
    "/{id_lideranca}",
    response_model=LiderancaResponse,
    summary="Atualiza dados de uma liderança"
)
async def atualizar_lideranca(
    id_lideranca: uuid.UUID,
    payload: LiderancaUpdate,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> LiderancaResponse:
    """Atualiza as informações da liderança no gabinete."""
    return await CabinetService.updateLeadership(connection, current_user.tenant_id, id_lideranca, payload)


@router.delete(
    "/{id_lideranca}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma liderança do gabinete"
)
async def remover_lideranca(
    id_lideranca: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> None:
    """Exclui a liderança do gabinete garantindo isolamento por tenant_id."""
    await CabinetService.deleteLeadership(connection, current_user.tenant_id, id_lideranca)
