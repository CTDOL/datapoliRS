from fastapi import APIRouter, Depends
import asyncpg
from app.core.dependencies import getDbConnection, get_current_user, require_role, bloquear_super_admin
from app.schemas.tema import TemaResponse, TemaUpdate
from app.schemas.user import UserInDB
from app.services import tema_service

router = APIRouter(
    prefix="/api/v1/gabinete/tema",
    tags=["Identidade visual do gabinete"],
    dependencies=[Depends(bloquear_super_admin)],
)


@router.get("", response_model=TemaResponse, summary="Cores do gabinete (null = padrão da plataforma)")
async def obter_tema(
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await tema_service.obter_tema(connection, current_user.tenant_id)


@router.put("", response_model=TemaResponse, summary="Define as cores do gabinete (só admin do gabinete)")
async def salvar_tema(
    payload: TemaUpdate,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await tema_service.salvar_tema(connection, current_user.tenant_id, payload)
