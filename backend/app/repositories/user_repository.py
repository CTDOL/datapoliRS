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
