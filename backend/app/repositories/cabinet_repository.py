import json
import uuid
import logging
from typing import List, Optional, Dict, Any
import asyncpg
from app.schemas.leadership import LiderancaCreate, LiderancaUpdate

logger = logging.getLogger("CabinetRepository")

# Campos simples de tb_gabinete_liderancas — tudo que NÃO é a relação N:N de
# municípios (essa é tratada à parte via tb_gabinete_lideranca_municipios).
_SIMPLE_FIELDS = ("nm_completo", "nr_telefone", "ds_email", "tp_influencia", "ds_observacoes", "is_ativo", "ds_foto_url")

_SELECT_COLUMNS = """
    l.id_lideranca,
    l.tenant_id,
    l.nm_completo,
    l.nr_telefone,
    l.ds_email,
    l.tp_influencia,
    l.ds_observacoes,
    l.is_ativo,
    l.ds_foto_url,
    l.created_at,
    COALESCE(
        json_agg(
            json_build_object(
                'cd_ibge_7', m.cd_ibge_7,
                'nm_municipio', m.nm_municipio,
                'latitude', ST_Y(ST_Centroid(m.geometria)),
                'longitude', ST_X(ST_Centroid(m.geometria))
            )
        ) FILTER (WHERE m.cd_ibge_7 IS NOT NULL),
        '[]'
    ) AS municipios
"""


def _parseMunicipiosJson(record: Dict[str, Any]) -> Dict[str, Any]:
    """asyncpg devolve json_agg como texto (sem codec de jsonb configurado) — decodifica antes do Pydantic ver."""
    row = dict(record)
    if isinstance(row.get("municipios"), str):
        row["municipios"] = json.loads(row["municipios"])
    return row


class CabinetRepository:
    """Repositório do Módulo de Gabinete Digital com isolamento Multi-Tenant estrito por tenant_id."""

    @staticmethod
    async def _setMunicipios(connection: asyncpg.Connection, leadershipId: uuid.UUID, municipios: List[str]) -> None:
        """Substitui integralmente o conjunto de municípios de atuação de uma liderança."""
        await connection.execute(
            "DELETE FROM tb_gabinete_lideranca_municipios WHERE id_lideranca = $1;",
            leadershipId
        )
        if municipios:
            codigosUnicos = list(dict.fromkeys(municipios))  # remove duplicatas preservando ordem
            await connection.executemany(
                """
                INSERT INTO tb_gabinete_lideranca_municipios (id_lideranca, cd_ibge_7)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING;
                """,
                [(leadershipId, codigo) for codigo in codigosUnicos]
            )

    @staticmethod
    async def createLeadership(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: LiderancaCreate
    ) -> Dict[str, Any]:
        """Cadastra uma nova liderança política vinculada obrigatoriamente ao tenant_id, com N municípios de atuação."""
        query = """
            INSERT INTO tb_gabinete_liderancas (
                tenant_id, nm_completo, nr_telefone,
                ds_email, tp_influencia, ds_observacoes, is_ativo
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id_lideranca;
        """
        try:
            async with connection.transaction():
                record = await connection.fetchrow(
                    query,
                    tenantId,
                    payload.nm_completo,
                    payload.nr_telefone,
                    payload.ds_email,
                    payload.tp_influencia,
                    payload.ds_observacoes,
                    payload.is_ativo
                )
                leadershipId = record["id_lideranca"]
                await CabinetRepository._setMunicipios(connection, leadershipId, payload.municipios)

            created = await CabinetRepository.getLeadershipById(connection, tenantId, leadershipId)
            return created
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao criar liderança para tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database insert error: {dbError}") from dbError

    @staticmethod
    async def listLeaderships(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        ibgeCode: Optional[str] = None,
        influenceCategory: Optional[str] = None,
        isActive: Optional[bool] = None,
        searchTerm: Optional[str] = None,
        page: int = 1,
        pageSize: int = 50
    ) -> tuple[List[Dict[str, Any]], int]:
        """Lista as lideranças de um gabinete paginadas, com filtros opcionais.

        Retorna (registros_da_página, total_de_registros). O total vem de uma
        contagem separada sobre l.id_lideranca (não dá para usar COUNT(*)
        OVER() aqui porque a query principal já agrega por GROUP BY).
        """
        conditions = ["l.tenant_id = $1"]
        params: List[Any] = [tenantId]
        paramIndex = 2

        if ibgeCode and ibgeCode.strip():
            conditions.append(f"""
                EXISTS (
                    SELECT 1 FROM tb_gabinete_lideranca_municipios x
                    WHERE x.id_lideranca = l.id_lideranca AND x.cd_ibge_7 = ${paramIndex}
                )
            """)
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

        if searchTerm and searchTerm.strip():
            conditions.append(f"l.nm_completo ILIKE ${paramIndex}")
            params.append(f"%{searchTerm.strip()}%")
            paramIndex += 1

        whereClause = " AND ".join(conditions)

        countQuery = f"SELECT COUNT(*) FROM tb_gabinete_liderancas l WHERE {whereClause};"

        limitParamIndex = paramIndex
        offsetParamIndex = paramIndex + 1
        dataParams = params + [pageSize, (page - 1) * pageSize]
        dataQuery = f"""
            SELECT {_SELECT_COLUMNS}
            FROM tb_gabinete_liderancas l
            LEFT JOIN tb_gabinete_lideranca_municipios lm ON lm.id_lideranca = l.id_lideranca
            LEFT JOIN tb_municipios m ON m.cd_ibge_7 = lm.cd_ibge_7
            WHERE {whereClause}
            GROUP BY l.id_lideranca
            ORDER BY l.nm_completo ASC
            LIMIT ${limitParamIndex} OFFSET ${offsetParamIndex};
        """
        try:
            total = await connection.fetchval(countQuery, *params)
            records = await connection.fetch(dataQuery, *dataParams)
            return [_parseMunicipiosJson(record) for record in records], total
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
        query = f"""
            SELECT {_SELECT_COLUMNS}
            FROM tb_gabinete_liderancas l
            LEFT JOIN tb_gabinete_lideranca_municipios lm ON lm.id_lideranca = l.id_lideranca
            LEFT JOIN tb_municipios m ON m.cd_ibge_7 = lm.cd_ibge_7
            WHERE l.tenant_id = $1 AND l.id_lideranca = $2
            GROUP BY l.id_lideranca;
        """
        try:
            record = await connection.fetchrow(query, tenantId, leadershipId)
            return _parseMunicipiosJson(record) if record else None
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
        """Atualiza dados cadastrais de uma liderança isolada pelo tenant_id.

        `municipios`, quando presente, é tratado à parte (substitui a relação
        N:N inteira) — não é uma coluna simples de tb_gabinete_liderancas.
        """
        payloadDict = payload.model_dump(exclude_unset=True)
        municipios = payloadDict.pop("municipios", None)

        try:
            async with connection.transaction():
                if payloadDict:
                    updateFields = []
                    params: List[Any] = [tenantId, leadershipId]
                    paramIndex = 3
                    for fieldName, fieldValue in payloadDict.items():
                        updateFields.append(f"{fieldName} = ${paramIndex}")
                        params.append(fieldValue)
                        paramIndex += 1

                    setClause = ", ".join(updateFields)
                    result = await connection.execute(
                        f"""
                        UPDATE tb_gabinete_liderancas
                        SET {setClause}
                        WHERE tenant_id = $1 AND id_lideranca = $2;
                        """,
                        *params
                    )
                    if result == "UPDATE 0":
                        return None

                if municipios is not None:
                    await CabinetRepository._setMunicipios(connection, leadershipId, municipios)

            return await CabinetRepository.getLeadershipById(connection, tenantId, leadershipId)
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao atualizar liderança {leadershipId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database update error: {dbError}") from dbError

    @staticmethod
    async def deleteLeadership(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        leadershipId: uuid.UUID
    ) -> bool:
        """Exclui uma liderança política com garantia de multi-tenancy (municípios em cascata via FK)."""
        query = "DELETE FROM tb_gabinete_liderancas WHERE tenant_id = $1 AND id_lideranca = $2;"
        try:
            result = await connection.execute(query, tenantId, leadershipId)
            return result == "DELETE 1"
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao deletar liderança {leadershipId} (tenant {tenantId}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database delete error: {dbError}") from dbError

    @staticmethod
    async def setFotoUrl(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        leadershipId: uuid.UUID,
        fotoUrl: str
    ) -> Optional[Dict[str, Any]]:
        """Grava a URL pública da foto após o upload ser salvo em disco."""
        result = await connection.execute(
            """
            UPDATE tb_gabinete_liderancas
            SET ds_foto_url = $3
            WHERE tenant_id = $1 AND id_lideranca = $2;
            """,
            tenantId, leadershipId, fotoUrl
        )
        if result == "UPDATE 0":
            return None
        return await CabinetRepository.getLeadershipById(connection, tenantId, leadershipId)
