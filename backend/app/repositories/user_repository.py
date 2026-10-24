import json
import uuid
import logging
from typing import Any, Dict, List, Optional
import asyncpg

logger = logging.getLogger("UserRepository")


class EmailAlreadyExistsError(Exception):
    """Levantado quando um e-mail já está em uso por outro usuário (tb_users.email é UNIQUE global)."""


class UserRepository:
    """Repositório de gestão de usuários (tb_users): equipe do gabinete e credenciais."""

    @staticmethod
    async def listByTenant(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[Dict[str, Any]]:
        query = """
            SELECT id, email, role, is_active, created_at
            FROM tb_users
            WHERE tenant_id = $1
            ORDER BY created_at ASC;
        """
        records = await connection.fetch(query, tenantId)
        return [dict(r) for r in records]

    @staticmethod
    async def getByIdAndTenant(
        connection: asyncpg.Connection, tenantId: uuid.UUID, userId: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        query = """
            SELECT id, email, role, is_active, created_at
            FROM tb_users
            WHERE tenant_id = $1 AND id = $2;
        """
        record = await connection.fetchrow(query, tenantId, userId)
        return dict(record) if record else None

    @staticmethod
    async def createInTenant(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        email: str,
        hashedPassword: str,
        role: str
    ) -> Dict[str, Any]:
        query = """
            INSERT INTO tb_users (tenant_id, email, hashed_password, is_active, role)
            VALUES ($1, $2, $3, TRUE, $4)
            RETURNING id, email, role, is_active, created_at;
        """
        try:
            record = await connection.fetchrow(query, tenantId, email, hashedPassword, role)
            return dict(record)
        except asyncpg.UniqueViolationError as dbError:
            raise EmailAlreadyExistsError(email) from dbError
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao criar usuário '{email}' no tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database insert error: {dbError}") from dbError

    @staticmethod
    async def updateInTenant(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        userId: uuid.UUID,
        role: Optional[str] = None,
        isActive: Optional[bool] = None,
        hashedPassword: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        setFields = []
        params: List[Any] = [tenantId, userId]
        paramIndex = 3

        if role is not None:
            setFields.append(f"role = ${paramIndex}")
            params.append(role)
            paramIndex += 1
        if isActive is not None:
            setFields.append(f"is_active = ${paramIndex}")
            params.append(isActive)
            paramIndex += 1
        if hashedPassword is not None:
            setFields.append(f"hashed_password = ${paramIndex}")
            params.append(hashedPassword)
            paramIndex += 1

        if not setFields:
            return await UserRepository.getByIdAndTenant(connection, tenantId, userId)

        setClause = ", ".join(setFields)
        query = f"""
            UPDATE tb_users
            SET {setClause}
            WHERE tenant_id = $1 AND id = $2
            RETURNING id, email, role, is_active, created_at;
        """
        try:
            record = await connection.fetchrow(query, *params)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao atualizar usuário {userId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database update error: {dbError}") from dbError

    @staticmethod
    async def getAuthByEmail(connection: asyncpg.Connection, email: str) -> Optional[Dict[str, Any]]:
        """Credenciais para o login. O e-mail é único na instância, então não filtra por tenant."""
        record = await connection.fetchrow(
            "SELECT email, hashed_password, is_active, tenant_id FROM tb_users WHERE email = $1",
            email,
        )
        return dict(record) if record else None

    @staticmethod
    async def getHashedPasswordById(connection: asyncpg.Connection, userId: uuid.UUID) -> Optional[str]:
        record = await connection.fetchrow("SELECT hashed_password FROM tb_users WHERE id = $1", userId)
        return record["hashed_password"] if record else None

    @staticmethod
    async def updatePassword(connection: asyncpg.Connection, userId: uuid.UUID, hashedPassword: str) -> None:
        """Grava a nova senha e encerra a obrigação de troca (must_change_password)."""
        await connection.execute(
            "UPDATE tb_users SET hashed_password = $1, must_change_password = FALSE WHERE id = $2",
            hashedPassword, userId,
        )

    @staticmethod
    async def getPreferencias(connection: asyncpg.Connection, userId: uuid.UUID) -> Dict[str, Any]:
        valor = await connection.fetchval("SELECT preferencias FROM tb_users WHERE id = $1", userId)
        if valor is None:
            return {}
        return json.loads(valor) if isinstance(valor, str) else dict(valor)

    @staticmethod
    async def mesclarPreferencias(connection: asyncpg.Connection, userId: uuid.UUID, preferencias: Dict[str, Any]) -> None:
        """Mescla no nível de chave de topo: as chaves enviadas substituem as gravadas, e as demais ficam como estão."""
        await connection.execute(
            "UPDATE tb_users SET preferencias = preferencias || $2::jsonb WHERE id = $1",
            userId, json.dumps(preferencias),
        )

    @staticmethod
    async def getForAuthentication(
        connection: asyncpg.Connection, email: str, tenantId: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Dados que o get_current_user precisa a cada requisição autenticada."""
        record = await connection.fetchrow(
            """
            SELECT id, email, is_active, tenant_id, role, must_change_password
            FROM tb_users
            WHERE email = $1 AND tenant_id = $2
            """,
            email, tenantId,
        )
        return dict(record) if record else None
