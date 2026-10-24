"""Preferências pessoais do usuário, guardadas no servidor (tb_users.preferencias).

Quem lê uma preferência gravada por outra versão do sistema, ou com dado corrompido,
recebe o padrão em vez de erro: a tela não pode quebrar por causa de uma preferência.
"""
import uuid

import asyncpg
from pydantic import ValidationError

from app.repositories.user_repository import UserRepository
from app.schemas.preferencias import PreferenciasUsuario, PreferenciasUsuarioUpdate


async def obter(connection: asyncpg.Connection, userId: uuid.UUID) -> PreferenciasUsuario:
    gravadas = await UserRepository.getPreferencias(connection, userId)
    try:
        return PreferenciasUsuario.model_validate(gravadas)
    except ValidationError:
        return PreferenciasUsuario()


async def salvar(connection: asyncpg.Connection, userId: uuid.UUID, payload: PreferenciasUsuarioUpdate) -> PreferenciasUsuario:
    alteracoes = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
    if alteracoes:
        await UserRepository.mesclarPreferencias(connection, userId, alteracoes)
    return await obter(connection, userId)
