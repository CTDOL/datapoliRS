import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
import asyncpg
from app.core.dependencies import getDbConnection, get_current_user, require_role
from app.schemas.user import UserInDB
from app.services.legislative_service import LegislativeService
from app.schemas.legislative import (
    ProposicaoExterna,
    ProjetoLeiImport,
    ProjetoLeiResponse,
    ProjetoLeiPageResponse,
    ObservadorAdd,
    ObservadorResponse,
)
from app.core.rate_limit import RateLimiter

router = APIRouter(
    prefix="/api/v1/gabinete/projetos-lei",
    tags=["Gabinete Digital & Projetos de Lei"],
    dependencies=[Depends(RateLimiter(times=30, seconds=1, configKey="legislative"))]
)


@router.get(
    "/buscar-externo",
    response_model=list[ProposicaoExterna],
    summary="Busca proposições por nome do parlamentar direto nas fontes oficiais (ALRS, Câmara, Senado)"
)
async def buscar_proposicoes_externas(
    nome: str = Query(..., min_length=3, description="Nome do parlamentar a buscar"),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> list[ProposicaoExterna]:
    """Agrega resultados de ALRS (scraping), Câmara e Senado (APIs oficiais) em uma
    única lista, marcando quais já foram importados por este gabinete."""
    return await LegislativeService.buscarExterno(connection, current_user.tenant_id, nome)


@router.post(
    "",
    response_model=ProjetoLeiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Importa uma proposição da fonte oficial para o gabinete"
)
async def importar_projeto_lei(
    payload: ProjetoLeiImport,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> ProjetoLeiResponse:
    """Revalida ementa/situação direto na fonte oficial antes de gravar — idempotente
    por (tenant, fonte, identificador_externo)."""
    return await LegislativeService.importarProjetoLei(connection, current_user.tenant_id, payload)


@router.get(
    "",
    response_model=ProjetoLeiPageResponse,
    summary="Lista os projetos de lei já importados pelo gabinete"
)
async def listar_projetos_lei(
    termo: Optional[str] = Query(None, description="Busca por ementa/autor/número"),
    fonte: Optional[str] = Query(None, description="Filtrar por fonte: ALRS, CAMARA ou SENADO"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> ProjetoLeiPageResponse:
    return await LegislativeService.listProjetosLei(
        connection=connection, tenantId=current_user.tenant_id,
        searchTerm=termo, fonte=fonte, page=page, pageSize=page_size,
    )


@router.get(
    "/{id_projeto_lei}",
    response_model=ProjetoLeiResponse,
    summary="Recupera um projeto de lei importado pelo ID"
)
async def obter_projeto_lei(
    id_projeto_lei: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> ProjetoLeiResponse:
    return await LegislativeService.getProjetoLeiById(connection, current_user.tenant_id, id_projeto_lei)


@router.delete(
    "/{id_projeto_lei}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um projeto de lei importado (requer papel admin)"
)
async def remover_projeto_lei(
    id_projeto_lei: uuid.UUID,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> None:
    await LegislativeService.deleteProjetoLei(connection, current_user.tenant_id, id_projeto_lei)


@router.get(
    "/{id_projeto_lei}/observadores",
    response_model=list[ObservadorResponse],
    summary="Lista as lideranças vinculadas como observadoras do projeto de lei"
)
async def listar_observadores(
    id_projeto_lei: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> list[ObservadorResponse]:
    return await LegislativeService.listObservadores(connection, current_user.tenant_id, id_projeto_lei)


@router.post(
    "/{id_projeto_lei}/observadores",
    response_model=list[ObservadorResponse],
    summary="Vincula uma liderança como observadora do projeto de lei"
)
async def adicionar_observador(
    id_projeto_lei: uuid.UUID,
    payload: ObservadorAdd,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> list[ObservadorResponse]:
    return await LegislativeService.addObservador(connection, current_user.tenant_id, id_projeto_lei, payload.id_lideranca)


@router.delete(
    "/{id_projeto_lei}/observadores/{id_lideranca}",
    response_model=list[ObservadorResponse],
    summary="Remove uma liderança da lista de observadores do projeto de lei"
)
async def remover_observador(
    id_projeto_lei: uuid.UUID,
    id_lideranca: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> list[ObservadorResponse]:
    return await LegislativeService.removeObservador(connection, current_user.tenant_id, id_projeto_lei, id_lideranca)
