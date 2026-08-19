import uuid
import logging
from typing import List, Optional, Dict, Any
import asyncpg
from app.schemas.leadership import LiderancaCreate, LiderancaUpdate

logger = logging.getLogger("CabinetRepository")


class CabinetRepository:
    """Repositório do Módulo de Gabinete Digital com isolamento Multi-Tenant estrito por tenant_id."""

    @staticmethod
    async def createLeadership(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: LiderancaCreate
    ) -> Dict[str, Any]:
        """Cadastra uma nova liderança política vinculada obrigatoriamente ao tenant_id."""
        query = """
            INSERT INTO tb_gabinete_liderancas (
                tenant_id, cd_ibge_7, nm_completo, nr_telefone,
                ds_email, tp_influencia, ds_observacoes, is_ativo
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING 
                id_lideranca, tenant_id, cd_ibge_7, nm_completo,
                nr_telefone, ds_email, tp_influencia, ds_observacoes,
                is_ativo, created_at;
        """
        try:
            record = await connection.fetchrow(
                query,
                tenantId,
                payload.cd_ibge_7,
                payload.nm_completo,
                payload.nr_telefone,
                payload.ds_email,
                payload.tp_influencia,
                payload.ds_observacoes,
                payload.is_ativo
            )
            return dict(record)
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao criar liderança para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database insert error: {dbError}") from dbError

    @staticmethod
    async def listLeaderships(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        ibgeCode: Optional[str] = None,
        influenceCategory: Optional[str] = None,
        isActive: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Lista todas as lideranças de um gabinete com filtros opcionais."""
        conditions = ["l.tenant_id = $1"]
        params: List[Any] = [tenantId]
        paramIndex = 2

        if ibgeCode and ibgeCode.strip():
            conditions.append(f"l.cd_ibge_7 = ${paramIndex}")
            params.append(ibgeCode.strip())
            paramIndex += 1

        if influenceCategory and influenceCategory.strip():
            conditions.append(f"l.tp_influencia = ${paramIndex}")
            params.append(influenceCategory.strip())
            paramIndex += 1

        if isActive is not None:
            conditions.append(f"l.is_ativo = ${paramIndex}")
            params.append(isActive)
            paramIndex += 1

        whereClause = " AND ".join(conditions)
        query = f"""
            SELECT 
                l.id_lideranca,
                l.tenant_id,
                l.cd_ibge_7,
                m.nm_municipio,
                l.nm_completo,
                l.nr_telefone,
                l.ds_email,
                l.tp_influencia,
                l.ds_observacoes,
                l.is_ativo,
                l.created_at
            FROM tb_gabinete_liderancas l
            LEFT JOIN tb_municipios m ON l.cd_ibge_7 = m.cd_ibge_7
            WHERE {whereClause}
            ORDER BY l.nm_completo ASC;
        """
        try:
            records = await connection.fetch(query, *params)
            return [dict(record) for record in records]
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao listar lideranças para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def getLeadershipById(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        leadershipId: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Busca uma liderança específica com garantia de isolamento por tenant_id."""
        query = """
            SELECT 
                l.id_lideranca,
                l.tenant_id,
                l.cd_ibge_7,
                m.nm_municipio,
                l.nm_completo,
                l.nr_telefone,
                l.ds_email,
                l.tp_influencia,
                l.ds_observacoes,
                l.is_ativo,
                l.created_at
            FROM tb_gabinete_liderancas l
            LEFT JOIN tb_municipios m ON l.cd_ibge_7 = m.cd_ibge_7
            WHERE l.tenant_id = $1 AND l.id_lideranca = $2;
        """
        try:
            record = await connection.fetchrow(query, tenantId, leadershipId)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao recuperar liderança {leadershipId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def updateLeadership(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        leadershipId: uuid.UUID,
        payload: LiderancaUpdate
    ) -> Optional[Dict[str, Any]]:
        """Atualiza dados cadastrais de uma liderança isolada pelo tenant_id."""
        updateFields = []
        params: List[Any] = [tenantId, leadershipId]
        paramIndex = 3

        payloadDict = payload.model_dump(exclude_unset=True)
        if not payloadDict:
            return await CabinetRepository.getLeadershipById(connection, tenantId, leadershipId)

        for fieldName, fieldValue in payloadDict.items():
            updateFields.append(f"{fieldName} = ${paramIndex}")
            params.append(fieldValue)
            paramIndex += 1

        setClause = ", ".join(updateFields)
        query = f"""
            UPDATE tb_gabinete_liderancas
            SET {setClause}
            WHERE tenant_id = $1 AND id_lideranca = $2
            RETURNING 
                id_lideranca, tenant_id, cd_ibge_7, nm_completo,
                nr_telefone, ds_email, tp_influencia, ds_observacoes,
                is_ativo, created_at;
        """
        try:
            record = await connection.fetchrow(query, *params)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao atualizar liderança {leadershipId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database update error: {dbError}") from dbError

    @staticmethod
    async def deleteLeadership(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        leadershipId: uuid.UUID
    ) -> bool:
        """Exclui uma liderança política com garantia de multi-tenancy."""
        query = "DELETE FROM tb_gabinete_liderancas WHERE tenant_id = $1 AND id_lideranca = $2;"
        try:
            result = await connection.execute(query, tenantId, leadershipId)
            return result == "DELETE 1"
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao deletar liderança {leadershipId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database delete error: {dbError}") from dbError
