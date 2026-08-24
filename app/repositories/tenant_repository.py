import uuid
import logging
from typing import Any, Dict, List, Optional
import asyncpg
from app.schemas.tenant import TenantProfileUpdate

logger = logging.getLogger("TenantRepository")


class TenantRepository:
    """Repositório do perfil do mandato (tb_tenants) e exportação de dados do gabinete."""

    PROFILE_QUERY = """
        SELECT
            t.id_tenant, t.nm_mandato, t.ds_cargo_mandato, t.cd_cargo,
            cg.ds_cargo, t.nr_partido, p.sg_partido, t.cd_ibge_base,
            m.nm_municipio AS nm_municipio_base, t.is_ativo, t.created_at
        FROM tb_tenants t
        LEFT JOIN tb_cargos cg ON t.cd_cargo = cg.cd_cargo
        LEFT JOIN tb_partidos p ON t.nr_partido = p.nr_partido
        LEFT JOIN tb_municipios m ON t.cd_ibge_base = m.cd_ibge_7
        WHERE t.id_tenant = $1;
    """

    @staticmethod
    async def getProfile(connection: asyncpg.Connection, tenantId: uuid.UUID) -> Optional[Dict[str, Any]]:
        try:
            record = await connection.fetchrow(TenantRepository.PROFILE_QUERY, tenantId)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao buscar perfil do tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def updateProfile(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: TenantProfileUpdate
    ) -> Optional[Dict[str, Any]]:
        """Atualiza o perfil do mandato. Quando cd_cargo é informado, ds_cargo_mandato
        (texto livre legado, ainda usado pelo bootstrap) é ressincronizado com o nome
        oficial do cargo para os dois campos nunca divergirem."""
        payloadDict = payload.model_dump(exclude_unset=True)
        if not payloadDict:
            return await TenantRepository.getProfile(connection, tenantId)

        setFields = []
        params: List[Any] = [tenantId]
        paramIndex = 2

        for fieldName, fieldValue in payloadDict.items():
            setFields.append(f"{fieldName} = ${paramIndex}")
            params.append(fieldValue)
            paramIndex += 1

        if "cd_cargo" in payloadDict and payloadDict["cd_cargo"] is not None:
            setFields.append(f"ds_cargo_mandato = COALESCE((SELECT ds_cargo FROM tb_cargos WHERE cd_cargo = ${paramIndex}), ds_cargo_mandato)")
            params.append(payloadDict["cd_cargo"])
            paramIndex += 1

        setClause = ", ".join(setFields)
        query = f"UPDATE tb_tenants SET {setClause} WHERE id_tenant = $1;"

        try:
            await connection.execute(query, *params)
            return await TenantRepository.getProfile(connection, tenantId)
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao atualizar perfil do tenant {tenantId}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database update error: {dbError}") from dbError

    @staticmethod
    async def getFormOptions(connection: asyncpg.Connection) -> Dict[str, List[Dict[str, Any]]]:
        """Listas de apoio (cargos, partidos, municípios) para os selects do formulário de perfil."""
        cargos = await connection.fetch("SELECT cd_cargo, ds_cargo FROM tb_cargos ORDER BY ds_cargo ASC;")
        partidos = await connection.fetch("SELECT nr_partido, sg_partido, nm_partido FROM tb_partidos ORDER BY sg_partido ASC;")
        municipios = await connection.fetch("SELECT cd_ibge_7, nm_municipio FROM tb_municipios ORDER BY nm_municipio ASC;")
        return {
            "cargos": [dict(r) for r in cargos],
            "partidos": [dict(r) for r in partidos],
            "municipios": [dict(r) for r in municipios],
        }

    @staticmethod
    async def exportLeaderships(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[Dict[str, Any]]:
        query = """
            SELECT l.nm_completo, m.nm_municipio, l.nr_telefone, l.ds_email,
                   l.tp_influencia, l.is_ativo, l.ds_observacoes, l.created_at
            FROM tb_gabinete_liderancas l
            LEFT JOIN tb_municipios m ON l.cd_ibge_7 = m.cd_ibge_7
            WHERE l.tenant_id = $1
            ORDER BY l.created_at ASC;
        """
        records = await connection.fetch(query, tenantId)
        return [dict(r) for r in records]

    @staticmethod
    async def exportAmendments(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[Dict[str, Any]]:
        query = """
            SELECT e.nr_emenda, e.ano_exercicio, m.nm_municipio, e.tp_emenda, e.ds_area,
                   e.ds_objeto, e.vl_indicado, e.vl_empenhado, e.vl_pago, e.tp_situacao,
                   e.ds_observacoes, e.created_at
            FROM tb_gabinete_emendas e
            LEFT JOIN tb_municipios m ON e.cd_ibge_7 = m.cd_ibge_7
            WHERE e.tenant_id = $1
            ORDER BY e.created_at ASC;
        """
        records = await connection.fetch(query, tenantId)
        return [dict(r) for r in records]
