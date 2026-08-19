import logging
from typing import List, Optional, Dict, Any
import asyncpg

logger = logging.getLogger("CandidateRepository")


class CandidateRepository:
    """Repositório de dados eleitorais e candidaturas (2022)."""

    async def searchCandidates(
        self,
        connection: asyncpg.Connection,
        searchTerm: Optional[str] = None,
        cargoCode: Optional[int] = None,
        partidoSigla: Optional[str] = None,
        candidateNumber: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Pesquisa candidaturas com filtros combinados e paginação."""
        conditions = ["1=1"]
        params: List[Any] = []
        paramIndex = 1

        if searchTerm and searchTerm.strip():
            wildcard = f"%{searchTerm.strip()}%"
            conditions.append(f"(unaccent(c.nm_urna_candidato) ILIKE unaccent(${paramIndex}) OR unaccent(c.nm_candidato) ILIKE unaccent(${paramIndex}))")
            params.append(wildcard)
            paramIndex += 1

        if cargoCode is not None:
            conditions.append(f"c.cd_cargo = ${paramIndex}")
            params.append(cargoCode)
            paramIndex += 1

        if partidoSigla and partidoSigla.strip():
            conditions.append(f"p.sg_partido = ${paramIndex}")
            params.append(partidoSigla.strip().upper())
            paramIndex += 1

        if candidateNumber is not None:
            conditions.append(f"c.nr_candidato = ${paramIndex}")
            params.append(candidateNumber)
            paramIndex += 1

        whereClause = " AND ".join(conditions)
        query = f"""
            SELECT 
                c.sq_candidato,
                c.nr_candidato,
                c.nm_urna_candidato,
                c.nm_candidato,
                c.cd_cargo,
                cg.ds_cargo,
                p.sg_partido,
                c.sg_uf,
                c.foto_url,
                c.ds_situacao_candidatura
            FROM tb_candidaturas c
            JOIN tb_cargos cg ON c.cd_cargo = cg.cd_cargo
            JOIN tb_partidos p ON c.nr_partido = p.nr_partido
            WHERE {whereClause}
            ORDER BY c.nm_urna_candidato ASC
            LIMIT ${paramIndex};
        """
        params.append(limit)

        try:
            records = await connection.fetch(query, *params)
            return [dict(record) for record in records]
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao buscar candidaturas: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    async def getCandidateBySq(
        self,
        connection: asyncpg.Connection,
        sqCandidato: int
    ) -> Optional[Dict[str, Any]]:
        """Recupera os detalhes de um candidato específico pelo sequencial TSE."""
        query = """
            SELECT 
                c.sq_candidato,
                c.cd_eleicao,
                c.nr_candidato,
                c.nm_urna_candidato,
                c.nm_candidato,
                c.cd_cargo,
                cg.ds_cargo,
                p.sg_partido,
                c.sg_uf,
                c.foto_url,
                c.ds_situacao_candidatura,
                c.vl_total_bens,
                c.st_reeleicao
            FROM tb_candidaturas c
            JOIN tb_cargos cg ON c.cd_cargo = cg.cd_cargo
            JOIN tb_partidos p ON c.nr_partido = p.nr_partido
            WHERE c.sq_candidato = $1;
        """
        try:
            record = await connection.fetchrow(query, sqCandidato)
            return dict(record) if record else None
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao recuperar candidato SQ {sqCandidato}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    async def listCargos(self, connection: asyncpg.Connection) -> List[Dict[str, Any]]:
        """Lista todos os cargos eleitorais cadastrados."""
        query = "SELECT cd_cargo, ds_cargo FROM tb_cargos ORDER BY cd_cargo ASC;"
        records = await connection.fetch(query)
        return [dict(record) for record in records]
