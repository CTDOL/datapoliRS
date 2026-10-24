import uuid
import logging
from typing import List, Optional, Dict, Any
import asyncpg
from app.schemas.task import TarefaCreate, TarefaUpdate

logger = logging.getLogger("TaskRepository")


def _resolverResponsaveis(idsResponsaveis: Optional[List[uuid.UUID]], idLegado: Optional[uuid.UUID]) -> List[uuid.UUID]:
    """Lista de responsáveis: a lista nova vence; sem ela, usa o campo legado de um responsável."""
    if idsResponsaveis is not None:
        return list(dict.fromkeys(idsResponsaveis))
    return [idLegado] if idLegado else []


class TaskRepository:
    """Repositório de Tarefas (vinculadas a Projeto de Lei, Emenda ou soltas), isolado por tenant_id."""

    @staticmethod
    async def _carregarResponsaveis(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaIds: List[uuid.UUID],
    ) -> Dict[uuid.UUID, List[Dict[str, Any]]]:
        if not tarefaIds:
            return {}
        records = await connection.fetch(
            """
            SELECT v.id_tarefa, l.id_lideranca, l.nm_completo, l.ds_foto_url
            FROM tb_gabinete_tarefa_liderancas v
            JOIN tb_gabinete_liderancas l ON l.id_lideranca = v.id_lideranca
            WHERE v.tenant_id = $1 AND v.id_tarefa = ANY($2::uuid[])
            ORDER BY l.nm_completo;
            """,
            tenantId,
            tarefaIds,
        )
        porTarefa: Dict[uuid.UUID, List[Dict[str, Any]]] = {}
        for record in records:
            porTarefa.setdefault(record["id_tarefa"], []).append({
                "id_lideranca": record["id_lideranca"],
                "nm_completo": record["nm_completo"],
                "ds_foto_url": record["ds_foto_url"],
            })
        return porTarefa

    @staticmethod
    async def _anexarResponsaveis(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        registros: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        porTarefa = await TaskRepository._carregarResponsaveis(
            connection, tenantId, [r["id_tarefa"] for r in registros]
        )
        for registro in registros:
            registro["responsaveis"] = porTarefa.get(registro["id_tarefa"], [])
        return registros

    @staticmethod
    async def _substituirResponsaveis(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaId: uuid.UUID,
        idsLiderancas: List[uuid.UUID],
    ) -> None:
        await connection.execute(
            "DELETE FROM tb_gabinete_tarefa_liderancas WHERE tenant_id = $1 AND id_tarefa = $2;",
            tenantId, tarefaId,
        )
        for idLideranca in idsLiderancas:
            await connection.execute(
                """
                INSERT INTO tb_gabinete_tarefa_liderancas (tenant_id, id_tarefa, id_lideranca)
                VALUES ($1, $2, $3);
                """,
                tenantId, tarefaId, idLideranca,
            )

    @staticmethod
    async def createTarefa(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: TarefaCreate,
    ) -> Dict[str, Any]:
        responsaveis = _resolverResponsaveis(payload.ids_responsaveis, payload.id_lideranca_responsavel)
        # A coluna legada guarda o primeiro responsável, para clientes que ainda a leem.
        idLegado = responsaveis[0] if responsaveis else None
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
            async with connection.transaction():
                record = await connection.fetchrow(
                    query,
                    tenantId,
                    payload.id_projeto_lei,
                    payload.id_emenda,
                    idLegado,
                    payload.titulo,
                    payload.descricao,
                    payload.prazo,
                    payload.tp_status,
                )
                await TaskRepository._substituirResponsaveis(connection, tenantId, record["id_tarefa"], responsaveis)
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
                   l.ds_foto_url AS ds_foto_url_responsavel,
                   t.titulo, t.descricao, t.prazo, t.tp_status, t.created_at
            FROM tb_gabinete_tarefas t
            LEFT JOIN tb_gabinete_liderancas l ON l.id_lideranca = t.id_lideranca_responsavel
            WHERE {whereClause}
            ORDER BY t.prazo ASC NULLS LAST, t.created_at DESC;
        """
        try:
            records = await connection.fetch(query, *params)
            registros = [dict(record) for record in records]
            return await TaskRepository._anexarResponsaveis(connection, tenantId, registros)
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
                   l.ds_foto_url AS ds_foto_url_responsavel,
                   t.titulo, t.descricao, t.prazo, t.tp_status, t.created_at
            FROM tb_gabinete_tarefas t
            LEFT JOIN tb_gabinete_liderancas l ON l.id_lideranca = t.id_lideranca_responsavel
            WHERE t.tenant_id = $1 AND t.id_tarefa = $2;
        """
        try:
            record = await connection.fetchrow(query, tenantId, tarefaId)
            if not record:
                return None
            registros = await TaskRepository._anexarResponsaveis(connection, tenantId, [dict(record)])
            return registros[0]
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

        # Responsáveis saem do SET da tarefa e vão para a tabela de vínculo.
        idsNovos: Optional[List[uuid.UUID]] = None
        if "ids_responsaveis" in payloadDict:
            idsNovos = _resolverResponsaveis(payloadDict.pop("ids_responsaveis"), None)
            payloadDict["id_lideranca_responsavel"] = idsNovos[0] if idsNovos else None
        elif "id_lideranca_responsavel" in payloadDict:
            legado = payloadDict["id_lideranca_responsavel"]
            idsNovos = [legado] if legado else []

        updateFields = []
        params: List[Any] = [tenantId, tarefaId]
        paramIndex = 3
        for fieldName, fieldValue in payloadDict.items():
            updateFields.append(f"{fieldName} = ${paramIndex}")
            params.append(fieldValue)
            paramIndex += 1

        try:
            async with connection.transaction():
                if updateFields:
                    setClause = ", ".join(updateFields)
                    query = f"""
                        UPDATE tb_gabinete_tarefas
                        SET {setClause}
                        WHERE tenant_id = $1 AND id_tarefa = $2
                        RETURNING id_tarefa;
                    """
                    atualizado = await connection.fetchrow(query, *params)
                    if not atualizado:
                        return None
                else:
                    existe = await connection.fetchval(
                        "SELECT 1 FROM tb_gabinete_tarefas WHERE tenant_id = $1 AND id_tarefa = $2;",
                        tenantId, tarefaId,
                    )
                    if not existe:
                        return None
                if idsNovos is not None:
                    await TaskRepository._substituirResponsaveis(connection, tenantId, tarefaId, idsNovos)
            return await TaskRepository.getTarefaById(connection, tenantId, tarefaId)
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
