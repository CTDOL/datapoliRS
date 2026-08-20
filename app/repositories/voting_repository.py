import logging
from typing import List, Optional, Dict, Any
import asyncpg

logger = logging.getLogger("VotingRepository")


class VotingRepository:
    """Repositório de dados analíticos de votação por município e zona eleitoral."""

    async def getVotesByCandidateSq(
        self,
        connection: asyncpg.Connection,
        sqCandidato: int
    ) -> List[Dict[str, Any]]:
        """Retorna a votação nominal agregada por município para um candidato (pelo SQ_CANDIDATO)."""
        query = """
            SELECT 
                f.cd_tse_municipio,
                m.nm_municipio,
                m.cd_ibge_7,
                SUM(f.qt_votos_nominais)::INT AS votos
            FROM tb_fato_votacao_munzona f
            LEFT JOIN tb_municipios m ON f.cd_tse_municipio = m.cd_tse
            WHERE f.sq_candidato = $1
            GROUP BY f.cd_tse_municipio, m.nm_municipio, m.cd_ibge_7
            ORDER BY votos DESC;
        """
        try:
            records = await connection.fetch(query, sqCandidato)
            return [dict(record) for record in records]
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao buscar votos do candidato SQ {sqCandidato}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    async def getVotesByCandidateNumberAndCargo(
        self,
        connection: asyncpg.Connection,
        candidateNumber: int,
        cargoCode: Optional[int] = None,
        ano: int = 2022
    ) -> Optional[Dict[str, Any]]:
        """Busca o candidato pelo número e retorna seu SQ e detalhes de votação."""
        candidateQuery = """
            SELECT 
                c.sq_candidato,
                c.cd_eleicao,
                c.nr_candidato,
                c.nm_urna_candidato,
                c.nm_candidato,
                cg.ds_cargo,
                p.sg_partido
            FROM tb_candidaturas c
            JOIN tb_cargos cg ON c.cd_cargo = cg.cd_cargo
            JOIN tb_partidos p ON c.nr_partido = p.nr_partido
            JOIN tb_eleicoes e ON c.cd_eleicao = e.cd_eleicao
            WHERE c.nr_candidato = $1
              AND ($2::INT IS NULL OR c.cd_cargo = $2::INT)
              AND e.ano_eleicao = $3
            ORDER BY c.sq_candidato DESC
            LIMIT 1;
        """
        try:
            candidateRecord = await connection.fetchrow(candidateQuery, candidateNumber, cargoCode, ano)
            if not candidateRecord:
                return None
            return dict(candidateRecord)
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao localizar candidato por número {candidateNumber}: {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError
