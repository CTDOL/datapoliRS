import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
import asyncpg
from app.core.dependencies import getDbConnection, get_current_user
from app.schemas.user import UserInDB
from app.services.task_service import TaskService
from app.schemas.task import TarefaCreate, TarefaUpdate, TarefaResponse
from app.core.rate_limit import RateLimiter

router = APIRouter(
    prefix="/api/v1/gabinete/tarefas",
    tags=["Gabinete Digital & Tarefas"],
    dependencies=[Depends(RateLimiter(times=30, seconds=1))]
)


@router.post(
    "",
    response_model=TarefaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma tarefa vinculada a um projeto de lei e/ou emenda"
)
async def criar_tarefa(
    payload: TarefaCreate,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> TarefaResponse:
    return await TaskService.createTarefa(connection, current_user.tenant_id, payload)


@router.get(
    "",
    response_model=list[TarefaResponse],
    summary="Lista tarefas do gabinete, opcionalmente filtradas por projeto de lei ou emenda"
)
async def listar_tarefas(
    id_projeto_lei: Optional[uuid.UUID] = Query(None),
    id_emenda: Optional[uuid.UUID] = Query(None),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> list[TarefaResponse]:
    return await TaskService.listTarefas(connection, current_user.tenant_id, id_projeto_lei, id_emenda)


@router.put(
    "/{id_tarefa}",
    response_model=TarefaResponse,
    summary="Atualiza uma tarefa (status, prazo, responsável, etc.)"
)
async def atualizar_tarefa(
    id_tarefa: uuid.UUID,
    payload: TarefaUpdate,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> TarefaResponse:
    return await TaskService.updateTarefa(connection, current_user.tenant_id, id_tarefa, payload)


@router.delete(
    "/{id_tarefa}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma tarefa"
)
async def remover_tarefa(
    id_tarefa: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> None:
    await TaskService.deleteTarefa(connection, current_user.tenant_id, id_tarefa)
