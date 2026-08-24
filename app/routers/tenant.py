import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Response, status
import asyncpg
from app.core.dependencies import getDbConnection, get_current_user, require_role
from app.core.rate_limit import RateLimiter
from app.schemas.user import UserInDB
from app.schemas.tenant import TenantProfileResponse, TenantProfileUpdate
from app.schemas.team import TeamMemberCreate, TeamMemberResponse, TeamMemberUpdate
from app.services.tenant_service import TenantService
from app.services.team_service import TeamService

router = APIRouter(
    prefix="/api/v1/gabinete",
    tags=["Configurações do Gabinete"],
    dependencies=[Depends(RateLimiter(times=30, seconds=1, configKey="tenant"))]
)


@router.get(
    "/perfil",
    response_model=TenantProfileResponse,
    summary="Recupera o perfil do mandato do gabinete autenticado"
)
async def obter_perfil_gabinete(
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> TenantProfileResponse:
    return await TenantService.getProfile(connection, current_user.tenant_id)


@router.put(
    "/perfil",
    response_model=TenantProfileResponse,
    summary="Atualiza o perfil do mandato (requer papel admin)"
)
async def atualizar_perfil_gabinete(
    payload: TenantProfileUpdate,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> TenantProfileResponse:
    return await TenantService.updateProfile(connection, current_user.tenant_id, payload)


@router.get(
    "/perfil/opcoes",
    summary="Listas de apoio (cargos, partidos, municípios) para o formulário de perfil"
)
async def obter_opcoes_perfil(
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> Dict[str, List[Dict[str, Any]]]:
    return await TenantService.getFormOptions(connection)


@router.get(
    "/usuarios",
    response_model=List[TeamMemberResponse],
    summary="Lista os usuários do gabinete (requer papel admin)"
)
async def listar_usuarios_gabinete(
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> List[TeamMemberResponse]:
    return await TeamService.listMembers(connection, current_user.tenant_id)


@router.post(
    "/usuarios",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Convida um novo membro para o gabinete (requer papel admin)"
)
async def convidar_usuario_gabinete(
    payload: TeamMemberCreate,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> TeamMemberResponse:
    return await TeamService.createMember(connection, current_user.tenant_id, payload)


@router.patch(
    "/usuarios/{id_user}",
    response_model=TeamMemberResponse,
    summary="Altera papel ou status de um usuário do gabinete (requer papel admin)"
)
async def atualizar_usuario_gabinete(
    id_user: uuid.UUID,
    payload: TeamMemberUpdate,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> TeamMemberResponse:
    return await TeamService.updateMember(
        connection, current_user.tenant_id, current_user.id, id_user, payload
    )


@router.get(
    "/exportar-dados",
    summary="Exporta as lideranças e emendas do gabinete em CSV (requer papel admin)",
    response_class=Response
)
async def exportar_dados_gabinete(
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> Response:
    csvContent = await TenantService.exportGabineteData(connection, current_user.tenant_id)
    return Response(
        content=csvContent,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gabinete_export.csv"}
    )
