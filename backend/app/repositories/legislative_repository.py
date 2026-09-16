import uuid
import logging
from typing import List, Optional, Dict, Any
import asyncpg

logger = logging.getLogger("LegislativeRepository")


class LegislativeRepository:
    """Repositório de Projetos de Lei e seus observadores, isolado por tenant_id."""

    @staticmethod
    async def importarProjetoLei(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        dados: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Grava o projeto de lei. Idempotente: se (tenant, fonte, identificador_externo)
        já existir, devolve o registro existente em vez de duplicar."""
        query = """
            INSERT INTO tb_gabinete_projetos_lei (
                tenant_id, fonte, identificador_externo, tipo, numero, ano,
                ementa, situacao, autor, url_fonte, data_apresentacao,
                ultima_sincronizacao
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
            ON CONFLICT (tenant_id, fonte, identificador_externo) DO UPDATE
                SET situacao = EXCLUDED.situacao,
                    ultima_sincronizacao = NOW()
            RETURNING
                id_projeto_lei, tenant_id, fonte, identificador_externo, tipo,
                numero, ano, ementa, situacao, autor, url_fonte,
                data_apresentacao, created_at, ultima_sincronizacao;
        """
        try:
            record = await connection.fetchrow(
                query,
                tenantId,
                dados["fonte"],
                dados["identificador_externo"],
                dados.get("tipo"),
                dados.get("numero"),
                dados.get("ano"),
                dados["ementa"],
                dados.get("situacao"),
                dados.get("autor"),
                dados.get("url_fonte"),
                dados.get("data_apresentacao"),
            )
            return dict(record)
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao importar projeto de lei para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database insert error: {dbError}") from dbError

    @staticmethod
    async def listProjetosLei(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        searchTerm: Optional[str] = None,
        fonte: Optional[str] = None,
        page: int = 1,
        pageSize: int = 50,
    ) -> tuple[List[Dict[str, Any]], int]:
        conditions = ["tenant_id = $1"]
        params: List[Any] = [tenantId]
        paramIndex = 2

        if fonte and fonte.strip():
            conditions.append(f"fonte = ${paramIndex}")
            params.append(fonte.strip().upper())
            paramIndex += 1

        if searchTerm and searchTerm.strip():
            conditions.append(f"(ementa ILIKE ${paramIndex} OR autor ILIKE ${paramIndex} OR numero ILIKE ${paramIndex})")
            params.append(f"%{searchTerm.strip()}%")
            paramIndex += 1

        whereClause = " AND ".join(conditions)
        countQuery = f"SELECT COUNT(*) FROM tb_gabinete_projetos_lei WHERE {whereClause};"

        limitParamIndex = paramIndex
        offsetParamIndex = paramIndex + 1
        dataParams = params + [pageSize, (page - 1) * pageSize]
        dataQuery = f"""
            SELECT id_projeto_lei, tenant_id, fonte, identificador_externo, tipo,
                   numero, ano, ementa, situacao, autor, url_fonte,
                   data_apresentacao, created_at, ultima_sincronizacao
            FROM tb_gabinete_projetos_lei
            WHERE {whereClause}
            ORDER BY created_at DESC
            LIMIT ${limitParamIndex} OFFSET ${offsetParamIndex};
        """
        try:
            total = await connection.fetchval(countQuery, *params)
            records = await connection.fetch(dataQuery, *dataParams)
            return [dict(record) for record in records], total
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao listar projetos de lei para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def sincronizarProjetoLei(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: uuid.UUID,
        situacao: Optional[str],
        ementa: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Atualiza só o que a fonte oficial pode mudar (situação e ementa) e carimba
        a conferência. Observadores e tarefas ficam intactos — é o que diferencia
        isto de apagar e reimportar."""
        query = """
            UPDATE tb_gabinete_projetos_lei
            SET situacao = $3,
                ementa = COALESCE($4, ementa),
                ultima_sincronizacao = NOW()
            WHERE tenant_id = $1 AND id_projeto_lei = $2
            RETURNING
                id_projeto_lei, tenant_id, fonte, identificador_externo, tipo,
                numero, ano, ementa, situacao, autor, url_fonte,
                data_apresentacao, created_at, ultima_sincronizacao;
        """
        try:
            record = await connection.fetchrow(query, tenantId, projetoLeiId, situacao, ementa)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao sincronizar projeto de lei {projetoLeiId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database update error: {dbError}") from dbError

    @staticmethod
    async def listChavesImportadas(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """Só as chaves de dedup (fonte, identificador_externo, id) — sem paginação,
        usado para marcar ja_importado na busca externa sem truncar em gabinetes grandes."""
        query = "SELECT fonte, identificador_externo, id_projeto_lei FROM tb_gabinete_projetos_lei WHERE tenant_id = $1;"
        try:
            records = await connection.fetch(query, tenantId)
            return [dict(record) for record in records]
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao listar chaves importadas para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def getProjetoLeiById(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        query = """
            SELECT id_projeto_lei, tenant_id, fonte, identificador_externo, tipo,
                   numero, ano, ementa, situacao, autor, url_fonte,
                   data_apresentacao, created_at, ultima_sincronizacao
            FROM tb_gabinete_projetos_lei
            WHERE tenant_id = $1 AND id_projeto_lei = $2;
        """
        try:
            record = await connection.fetchrow(query, tenantId, projetoLeiId)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao buscar projeto de lei {projetoLeiId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def deleteProjetoLei(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: uuid.UUID,
    ) -> bool:
        query = "DELETE FROM tb_gabinete_projetos_lei WHERE tenant_id = $1 AND id_projeto_lei = $2;"
        try:
            result = await connection.execute(query, tenantId, projetoLeiId)
            return result == "DELETE 1"
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao deletar projeto de lei {projetoLeiId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database delete error: {dbError}") from dbError

    @staticmethod
    async def addObservador(
        connection: asyncpg.Connection,
        projetoLeiId: uuid.UUID,
        liderancaId: uuid.UUID,
    ) -> None:
        query = """
            INSERT INTO tb_gabinete_projeto_lei_observadores (id_projeto_lei, id_lideranca)
            VALUES ($1, $2)
            ON CONFLICT (id_projeto_lei, id_lideranca) DO NOTHING;
        """
        try:
            await connection.execute(query, projetoLeiId, liderancaId)
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao adicionar observador {liderancaId} ao PL {projetoLeiId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database insert error: {dbError}") from dbError

    @staticmethod
    async def removeObservador(
        connection: asyncpg.Connection,
        projetoLeiId: uuid.UUID,
        liderancaId: uuid.UUID,
    ) -> bool:
        query = """
            DELETE FROM tb_gabinete_projeto_lei_observadores
            WHERE id_projeto_lei = $1 AND id_lideranca = $2;
        """
        try:
            result = await connection.execute(query, projetoLeiId, liderancaId)
            return result == "DELETE 1"
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao remover observador {liderancaId} do PL {projetoLeiId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database delete error: {dbError}") from dbError

    @staticmethod
    async def listObservadores(
        connection: asyncpg.Connection,
        projetoLeiId: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT l.id_lideranca, l.nm_completo
            FROM tb_gabinete_projeto_lei_observadores o
            JOIN tb_gabinete_liderancas l ON l.id_lideranca = o.id_lideranca
            WHERE o.id_projeto_lei = $1
            ORDER BY l.nm_completo ASC;
        """
        try:
            records = await connection.fetch(query, projetoLeiId)
            return [dict(record) for record in records]
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao listar observadores do PL {projetoLeiId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError
