import uuid
from typing import List

import asyncpg
from fastapi import APIRouter, Depends, status

from app.core.dependencies import getDbConnection, require_role
from app.schemas.plataforma import GabineteCreate, GabineteResumo, GabineteStatusUpdate, SenhaAdminUpdate
from app.schemas.user import UserInDB
from app.services import plataforma_service

router = APIRouter(
    prefix="/api/v1/plataforma",
    tags=["Plataforma (super-admin)"],
)


@router.get("/gabinetes", response_model=List[GabineteResumo], summary="Lista os gabinetes da plataforma")
async def listar_gabinetes(
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await plataforma_service.listar_gabinetes(connection)


@router.post("/gabinetes", status_code=status.HTTP_201_CREATED, summary="Cria um gabinete e o seu administrador")
async def criar_gabinete(
    payload: GabineteCreate,
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await plataforma_service.criar_gabinete(connection, payload)


@router.patch("/gabinetes/{id_tenant}", status_code=status.HTTP_204_NO_CONTENT,
              summary="Ativa ou desativa um gabinete e os acessos dos seus usuários")
async def alterar_status_gabinete(
    id_tenant: uuid.UUID,
    payload: GabineteStatusUpdate,
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    await plataforma_service.alterar_status_gabinete(connection, id_tenant, payload.is_ativo)


@router.post("/gabinetes/{id_tenant}/admin/senha", status_code=status.HTTP_204_NO_CONTENT,
             summary="Redefine a senha de um administrador do gabinete")
async def redefinir_senha_admin(
    id_tenant: uuid.UUID,
    payload: SenhaAdminUpdate,
    current_user: UserInDB = Depends(require_role(["super_admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    await plataforma_service.redefinir_senha_admin(connection, id_tenant, payload.email_admin, payload.senha_nova)
