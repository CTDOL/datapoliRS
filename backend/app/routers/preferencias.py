from fastapi import APIRouter, Depends
import asyncpg
from app.core.dependencies import getDbConnection, get_current_user
from app.schemas.preferencias import PreferenciasUsuario, PreferenciasUsuarioUpdate
from app.schemas.user import UserInDB
from app.services import preferencias_service

router = APIRouter(
    prefix="/api/v1/usuario/preferencias",
    tags=["Preferências do usuário"],
)


@router.get("", response_model=PreferenciasUsuario, summary="Preferências pessoais do usuário logado")
async def obter_preferencias(
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await preferencias_service.obter(connection, current_user.id)


@router.put("", response_model=PreferenciasUsuario, summary="Grava as preferências pessoais do usuário logado")
async def salvar_preferencias(
    payload: PreferenciasUsuarioUpdate,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await preferencias_service.salvar(connection, current_user.id, payload)
