import uuid
import logging
from typing import List, Optional, Dict, Any
import asyncpg
from app.schemas.budget_amendment import EmendaCreate, EmendaUpdate

logger = logging.getLogger("AmendmentRepository")


class AmendmentRepository:
    """Repositório de Emendas Orçamentárias com isolamento Multi-Tenant estrito por tenant_id."""

    @staticmethod
    async def createAmendment(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: EmendaCreate
    ) -> Dict[str, Any]:
        """Cadastra uma nova emenda orçamentária vinculada obrigatoriamente ao tenant_id."""
        query = """
            INSERT INTO tb_gabinete_emendas (
                tenant_id, cd_ibge_7, nr_emenda, ano_exercicio, tp_emenda,
                ds_area, ds_objeto, vl_indicado, vl_empenhado, vl_pago,
                tp_situacao, ds_observacoes
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING
                id_emenda, tenant_id, cd_ibge_7, nr_emenda, ano_exercicio, tp_emenda,
                ds_area, ds_objeto, vl_indicado, vl_empenhado, vl_pago,
                tp_situacao, ds_observacoes, created_at;
        """
        try:
            record = await connection.fetchrow(
                query,
                tenantId,
                payload.cd_ibge_7,
                payload.nr_emenda,
                payload.ano_exercicio,
                payload.tp_emenda,
                payload.ds_area,
                payload.ds_objeto,
                payload.vl_indicado,
                payload.vl_empenhado,
                payload.vl_pago,
                payload.tp_situacao,
                payload.ds_observacoes,
            )
            return dict(record)
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao criar emenda para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database insert error: {dbError}") from dbError

    @staticmethod
    async def listAmendments(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        ibgeCode: Optional[str] = None,
        anoExercicio: Optional[int] = None,
        tpSituacao: Optional[str] = None,
        searchTerm: Optional[str] = None,
        page: int = 1,
        pageSize: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """Lista as emendas de um gabinete paginadas, com filtros opcionais.

        Retorna (registros_da_página, total_de_registros).
        """
        conditions = ["e.tenant_id = $1"]
        params: List[Any] = [tenantId]
        paramIndex = 2

        if ibgeCode and ibgeCode.strip():
            conditions.append(f"e.cd_ibge_7 = ${paramIndex}")
            params.append(ibgeCode.strip())
            paramIndex += 1

        if anoExercicio is not None:
            conditions.append(f"e.ano_exercicio = ${paramIndex}")
            params.append(anoExercicio)
            paramIndex += 1

        if tpSituacao and tpSituacao.strip():
            conditions.append(f"e.tp_situacao = ${paramIndex}")
            params.append(tpSituacao.strip())
            paramIndex += 1

        if searchTerm and searchTerm.strip():
            conditions.append(f"(e.ds_objeto ILIKE ${paramIndex} OR e.nr_emenda ILIKE ${paramIndex})")
            params.append(f"%{searchTerm.strip()}%")
            paramIndex += 1

        whereClause = " AND ".join(conditions)

        countQuery = f"SELECT COUNT(*) FROM tb_gabinete_emendas e WHERE {whereClause};"

        limitParamIndex = paramIndex
        offsetParamIndex = paramIndex + 1
        dataParams = params + [pageSize, (page - 1) * pageSize]
        dataQuery = f"""
            SELECT
                e.id_emenda,
                e.tenant_id,
                e.cd_ibge_7,
                m.nm_municipio,
                e.nr_emenda,
                e.ano_exercicio,
                e.tp_emenda,
                e.ds_area,
                e.ds_objeto,
                e.vl_indicado,
                e.vl_empenhado,
                e.vl_pago,
                e.tp_situacao,
                e.ds_observacoes,
                e.created_at
            FROM tb_gabinete_emendas e
            LEFT JOIN tb_municipios m ON e.cd_ibge_7 = m.cd_ibge_7
            WHERE {whereClause}
            ORDER BY e.created_at DESC
            LIMIT ${limitParamIndex} OFFSET ${offsetParamIndex};
        """
        try:
            total = await connection.fetchval(countQuery, *params)
            records = await connection.fetch(dataQuery, *dataParams)
            return [dict(record) for record in records], total
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao listar emendas para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def getAmendmentById(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        amendmentId: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Busca uma emenda específica com garantia de isolamento por tenant_id."""
        query = """
            SELECT
                e.id_emenda,
                e.tenant_id,
                e.cd_ibge_7,
                m.nm_municipio,
                e.nr_emenda,
                e.ano_exercicio,
                e.tp_emenda,
                e.ds_area,
                e.ds_objeto,
                e.vl_indicado,
                e.vl_empenhado,
                e.vl_pago,
                e.tp_situacao,
                e.ds_observacoes,
                e.created_at
            FROM tb_gabinete_emendas e
            LEFT JOIN tb_municipios m ON e.cd_ibge_7 = m.cd_ibge_7
            WHERE e.tenant_id = $1 AND e.id_emenda = $2;
        """
        try:
            record = await connection.fetchrow(query, tenantId, amendmentId)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao recuperar emenda {amendmentId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def updateAmendment(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        amendmentId: uuid.UUID,
        payload: EmendaUpdate
    ) -> Optional[Dict[str, Any]]:
        """Atualiza dados de uma emenda isolada pelo tenant_id."""
        updateFields = []
        params: List[Any] = [tenantId, amendmentId]
        paramIndex = 3

        payloadDict = payload.model_dump(exclude_unset=True)
        if not payloadDict:
            return await AmendmentRepository.getAmendmentById(connection, tenantId, amendmentId)

        for fieldName, fieldValue in payloadDict.items():
            updateFields.append(f"{fieldName} = ${paramIndex}")
            params.append(fieldValue)
            paramIndex += 1

        setClause = ", ".join(updateFields)
        query = f"""
            UPDATE tb_gabinete_emendas
            SET {setClause}
            WHERE tenant_id = $1 AND id_emenda = $2
            RETURNING
                id_emenda, tenant_id, cd_ibge_7, nr_emenda, ano_exercicio, tp_emenda,
                ds_area, ds_objeto, vl_indicado, vl_empenhado, vl_pago,
                tp_situacao, ds_observacoes, created_at;
        """
        try:
            record = await connection.fetchrow(query, *params)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao atualizar emenda {amendmentId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database update error: {dbError}") from dbError

    @staticmethod
    async def deleteAmendment(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        amendmentId: uuid.UUID
    ) -> bool:
        """Exclui uma emenda orçamentária com garantia de multi-tenancy."""
        query = "DELETE FROM tb_gabinete_emendas WHERE tenant_id = $1 AND id_emenda = $2;"
        try:
            result = await connection.execute(query, tenantId, amendmentId)
            return result == "DELETE 1"
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao deletar emenda {amendmentId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database delete error: {dbError}") from dbError

    @staticmethod
    async def getKpis(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        anoExercicio: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Agrega totais financeiros e contagem por situação, isolado por tenant_id."""
        conditions = ["tenant_id = $1"]
        params: List[Any] = [tenantId]
        if anoExercicio is not None:
            conditions.append("ano_exercicio = $2")
            params.append(anoExercicio)
        whereClause = " AND ".join(conditions)

        totalsQuery = f"""
            SELECT
                COUNT(*) AS total_emendas,
                COALESCE(SUM(vl_indicado), 0) AS vl_total_indicado,
                COALESCE(SUM(vl_empenhado), 0) AS vl_total_empenhado,
                COALESCE(SUM(vl_pago), 0) AS vl_total_pago
            FROM tb_gabinete_emendas
            WHERE {whereClause};
        """
        situacaoQuery = f"""
            SELECT tp_situacao, COUNT(*) AS quantidade
            FROM tb_gabinete_emendas
            WHERE {whereClause}
            GROUP BY tp_situacao;
        """
        try:
            totals = await connection.fetchrow(totalsQuery, *params)
            situacaoRows = await connection.fetch(situacaoQuery, *params)
            return {
                "total_emendas": totals["total_emendas"],
                "vl_total_indicado": totals["vl_total_indicado"],
                "vl_total_empenhado": totals["vl_total_empenhado"],
                "vl_total_pago": totals["vl_total_pago"],
                "por_situacao": {row["tp_situacao"]: row["quantidade"] for row in situacaoRows},
            }
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao calcular KPIs de emendas (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError
