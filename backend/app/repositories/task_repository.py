import uuid
import logging
from typing import List, Optional, Dict, Any
import asyncpg
from app.schemas.task import TarefaCreate, TarefaUpdate

logger = logging.getLogger("TaskRepository")


class TaskRepository:
    """Repositório de Tarefas (vinculadas a Projeto de Lei e/ou Emenda), isolado por tenant_id."""

    @staticmethod
    async def createTarefa(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: TarefaCreate,
    ) -> Dict[str, Any]:
        query = """
            INSERT INTO tb_gabinete_tarefas (
                tenant_id, id_projeto_lei, id_emenda, id_lideranca_responsavel,
                titulo, descricao, prazo, tp_status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id_tarefa, tenant_id, id_projeto_lei, id_emenda,
                      id_lideranca_responsavel, titulo, descricao, prazo,
                      tp_status, created_at;
        """
        try:
            record = await connection.fetchrow(
                query,
                tenantId,
                payload.id_projeto_lei,
                payload.id_emenda,
                payload.id_lideranca_responsavel,
                payload.titulo,
                payload.descricao,
                payload.prazo,
                payload.tp_status,
            )
            return dict(record)
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao criar tarefa para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database insert error: {dbError}") from dbError

    @staticmethod
    async def listTarefas(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: Optional[uuid.UUID] = None,
        emendaId: Optional[uuid.UUID] = None,
    ) -> List[Dict[str, Any]]:
        conditions = ["t.tenant_id = $1"]
        params: List[Any] = [tenantId]
        paramIndex = 2

        if projetoLeiId is not None:
            conditions.append(f"t.id_projeto_lei = ${paramIndex}")
            params.append(projetoLeiId)
            paramIndex += 1

        if emendaId is not None:
            conditions.append(f"t.id_emenda = ${paramIndex}")
            params.append(emendaId)
            paramIndex += 1

        whereClause = " AND ".join(conditions)
        query = f"""
            SELECT t.id_tarefa, t.tenant_id, t.id_projeto_lei, t.id_emenda,
                   t.id_lideranca_responsavel, l.nm_completo AS nm_lideranca_responsavel,
                   t.titulo, t.descricao, t.prazo, t.tp_status, t.created_at
            FROM tb_gabinete_tarefas t
            LEFT JOIN tb_gabinete_liderancas l ON l.id_lideranca = t.id_lideranca_responsavel
            WHERE {whereClause}
            ORDER BY t.prazo ASC NULLS LAST, t.created_at DESC;
        """
        try:
            records = await connection.fetch(query, *params)
            return [dict(record) for record in records]
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao listar tarefas para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def getTarefaById(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaId: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        query = """
            SELECT t.id_tarefa, t.tenant_id, t.id_projeto_lei, t.id_emenda,
                   t.id_lideranca_responsavel, l.nm_completo AS nm_lideranca_responsavel,
                   t.titulo, t.descricao, t.prazo, t.tp_status, t.created_at
            FROM tb_gabinete_tarefas t
            LEFT JOIN tb_gabinete_liderancas l ON l.id_lideranca = t.id_lideranca_responsavel
            WHERE t.tenant_id = $1 AND t.id_tarefa = $2;
        """
        try:
            record = await connection.fetchrow(query, tenantId, tarefaId)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao buscar tarefa {tarefaId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def updateTarefa(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaId: uuid.UUID,
        payload: TarefaUpdate,
    ) -> Optional[Dict[str, Any]]:
        payloadDict = payload.model_dump(exclude_unset=True)
        if not payloadDict:
            return await TaskRepository.getTarefaById(connection, tenantId, tarefaId)

        updateFields = []
        params: List[Any] = [tenantId, tarefaId]
        paramIndex = 3
        for fieldName, fieldValue in payloadDict.items():
            updateFields.append(f"{fieldName} = ${paramIndex}")
            params.append(fieldValue)
            paramIndex += 1

        setClause = ", ".join(updateFields)
        query = f"""
            UPDATE tb_gabinete_tarefas
            SET {setClause}
            WHERE tenant_id = $1 AND id_tarefa = $2
            RETURNING id_tarefa, tenant_id, id_projeto_lei, id_emenda,
                      id_lideranca_responsavel, titulo, descricao, prazo,
                      tp_status, created_at;
        """
        try:
            record = await connection.fetchrow(query, *params)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao atualizar tarefa {tarefaId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database update error: {dbError}") from dbError

    @staticmethod
    async def deleteTarefa(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaId: uuid.UUID,
    ) -> bool:
        query = "DELETE FROM tb_gabinete_tarefas WHERE tenant_id = $1 AND id_tarefa = $2;"
        try:
            result = await connection.execute(query, tenantId, tarefaId)
            return result == "DELETE 1"
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao deletar tarefa {tarefaId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database delete error: {dbError}") from dbError
