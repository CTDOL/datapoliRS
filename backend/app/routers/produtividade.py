import uuid

import asyncpg
from fastapi import APIRouter, Depends, status

from app.core.dependencies import bloquear_super_admin, get_current_user, getDbConnection, require_role
from app.core.rate_limit import RateLimiter
from app.schemas.produtividade import ComentarioCreate, ComentarioResponse, ProdutividadeResponse
from app.schemas.user import UserInDB
from app.services.produtividade_service import ProdutividadeService

router = APIRouter(
    prefix="/api/v1/gabinete",
    tags=["Gabinete Digital & Tarefas"],
    dependencies=[Depends(RateLimiter(times=30, seconds=1, configKey="tasks")), Depends(bloquear_super_admin)],
)


@router.get(
    "/tarefas/{id_tarefa}/comentarios",
    response_model=list[ComentarioResponse],
    summary="Comentários de execução de uma tarefa (todos os papéis do gabinete leem)",
)
async def listar_comentarios(
    id_tarefa: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
) -> list[ComentarioResponse]:
    return await ProdutividadeService.listarComentarios(connection, current_user.tenant_id, id_tarefa)


@router.post(
    "/tarefas/{id_tarefa}/comentarios",
    response_model=ComentarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um comentário de execução na tarefa (admin e operador)",
)
async def criar_comentario(
    id_tarefa: uuid.UUID,
    payload: ComentarioCreate,
    current_user: UserInDB = Depends(require_role(["admin", "operador"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
) -> ComentarioResponse:
    return await ProdutividadeService.criarComentario(
        connection, current_user.tenant_id, id_tarefa, current_user.email, payload.texto
    )


@router.get(
    "/produtividade",
    response_model=ProdutividadeResponse,
    summary="Painel de produtividade do gabinete (somente admin)",
)
async def painel_produtividade(
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
) -> ProdutividadeResponse:
    return await ProdutividadeService.painelProdutividade(connection, current_user.tenant_id)
