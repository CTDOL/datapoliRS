"""Regras do super-admin da plataforma (ADR 037).

O super-admin cria, lista, desativa gabinetes e redefine a senha de um admin.
Não lê nem altera registros de liderança, emenda, projeto de lei ou tarefa.
"""
import uuid
from typing import Any, Dict, List

import asyncpg
from fastapi import HTTPException, status

from app.schemas.plataforma import GabineteCreate
from app.services.auth_service import AuthService

# Gabinete que hospeda a conta do super-admin. Nunca aparece na listagem nem pode ser desativado.
PLATAFORMA_TENANT_ID = uuid.uuid5(uuid.NAMESPACE_URL, "datapolirs:ctdol-plataforma")


def _impedir_plataforma(id_tenant: uuid.UUID) -> None:
    if id_tenant == PLATAFORMA_TENANT_ID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="O gabinete da plataforma não pode ser alterado por aqui.")


async def listar_gabinetes(connection: asyncpg.Connection) -> List[Dict[str, Any]]:
    linhas = await connection.fetch(
        """
        SELECT t.id_tenant, t.nm_mandato, t.ds_cargo_mandato, t.is_ativo,
               (SELECT string_agg(u.email, ', ') FROM tb_users u
                 WHERE u.tenant_id = t.id_tenant AND u.role = 'admin') AS emails_admin
          FROM tb_tenants t
         WHERE t.id_tenant <> $1
         ORDER BY t.created_at
        """,
        PLATAFORMA_TENANT_ID,
    )
    return [{**dict(l), "id_tenant": str(l["id_tenant"])} for l in linhas]


async def criar_gabinete(connection: asyncpg.Connection, payload: GabineteCreate) -> Dict[str, Any]:
    existe = await connection.fetchval("SELECT 1 FROM tb_users WHERE email = $1", payload.email_admin)
    if existe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Já existe um usuário com este e-mail.")

    id_tenant = uuid.uuid4()
    hashed = AuthService.get_password_hash(payload.senha_inicial)
    async with connection.transaction():
        await connection.execute(
            """
            INSERT INTO tb_tenants (id_tenant, nm_mandato, ds_cargo_mandato, cd_ibge_base)
            VALUES ($1, $2, $3, $4)
            """,
            id_tenant, payload.nm_mandato, payload.ds_cargo_mandato, payload.cd_ibge_base,
        )
        await connection.execute(
            """
            INSERT INTO tb_users (tenant_id, email, hashed_password, is_active, role, must_change_password)
            VALUES ($1, $2, $3, TRUE, 'admin', TRUE)
            """,
            id_tenant, payload.email_admin, hashed,
        )
    return {"id_tenant": str(id_tenant), "nm_mandato": payload.nm_mandato, "email_admin": payload.email_admin}


async def alterar_status_gabinete(connection: asyncpg.Connection, id_tenant: uuid.UUID, ativo: bool) -> None:
    _impedir_plataforma(id_tenant)
    async with connection.transaction():
        atualizado = await connection.execute(
            "UPDATE tb_tenants SET is_ativo = $2 WHERE id_tenant = $1", id_tenant, ativo
        )
        if atualizado == "UPDATE 0":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gabinete não encontrado.")
        # Desativar o gabinete desativa os acessos dos seus usuários: o login e as rotas recusam usuário inativo.
        await connection.execute(
            "UPDATE tb_users SET is_active = $2 WHERE tenant_id = $1", id_tenant, ativo
        )


async def redefinir_senha_admin(connection: asyncpg.Connection, id_tenant: uuid.UUID,
                                email_admin: str, senha_nova: str) -> None:
    _impedir_plataforma(id_tenant)
    hashed = AuthService.get_password_hash(senha_nova)
    atualizado = await connection.execute(
        """
        UPDATE tb_users SET hashed_password = $3, must_change_password = TRUE
         WHERE tenant_id = $1 AND email = $2 AND role = 'admin'
        """,
        id_tenant, email_admin, hashed,
    )
    if atualizado == "UPDATE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Administrador não encontrado neste gabinete.")
