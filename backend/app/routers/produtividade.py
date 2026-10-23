import uuid

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import bloquear_super_admin, get_current_user, getDbConnection, require_role
from app.core.rate_limit import RateLimiter
from app.repositories.produtividade_repository import ProdutividadeRepository
from app.schemas.produtividade import ComentarioCreate, ComentarioResponse, ProdutividadeResponse, TotaisTarefas, CargaResponsavel
from app.schemas.user import UserInDB

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
    if not await ProdutividadeRepository.tarefaDoTenant(connection, current_user.tenant_id, id_tarefa):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada para este gabinete.")
    registros = await ProdutividadeRepository.listarComentarios(connection, current_user.tenant_id, id_tarefa)
    return [ComentarioResponse(**r) for r in registros]


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
    if not await ProdutividadeRepository.tarefaDoTenant(connection, current_user.tenant_id, id_tarefa):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada para este gabinete.")
    registro = await ProdutividadeRepository.criarComentario(
        connection, current_user.tenant_id, id_tarefa, current_user.email, payload.texto.strip(),
    )
    return ComentarioResponse(**registro)


@router.get(
    "/produtividade",
    response_model=ProdutividadeResponse,
    summary="Painel de produtividade do gabinete (somente admin)",
)
async def painel_produtividade(
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
) -> ProdutividadeResponse:
    tenant = current_user.tenant_id
    totais = await ProdutividadeRepository.totaisTarefas(connection, tenant)
    carga = await ProdutividadeRepository.cargaPorResponsavel(connection, tenant)
    return ProdutividadeResponse(
        tarefas=TotaisTarefas(**totais),
        por_responsavel=[CargaResponsavel(**c) for c in carga],
        comentarios_ultimos_7_dias=await ProdutividadeRepository.comentariosRecentes(connection, tenant),
        projetos_lei=await ProdutividadeRepository.contar(connection, tenant, "tb_gabinete_projetos_lei"),
        emendas=await ProdutividadeRepository.contar(connection, tenant, "tb_gabinete_emendas"),
    )
