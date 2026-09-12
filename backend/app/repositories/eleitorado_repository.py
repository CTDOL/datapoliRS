import logging
from typing import List, Dict, Any, Optional
import asyncpg

logger = logging.getLogger("EleitoradoRepository")


class EleitoradoRepository:
    """Repositório de eleitorado apto, comparecimento e abstenções por município.

    Fonte independente de tb_fato_votacao_munzona (que só traz votos nominais
    por candidato): vem do dataset TSE detalhe_votacao_munzona, agregado por
    zona em tb_fato_comparecimento_munzona.
    """

    @staticmethod
    async def getComparecimentoByMunicipio(
        connection: asyncpg.Connection,
        ano: int
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT
                f.cd_tse_municipio,
                COALESCE(m.nm_municipio, MAX(f.nm_municipio_tse)) AS nm_municipio,
                m.cd_ibge_7,
                SUM(f.qt_aptos)::INT AS qt_aptos,
                SUM(f.qt_comparecimento)::INT AS qt_comparecimento,
                SUM(f.qt_abstencoes)::INT AS qt_abstencoes
            FROM tb_fato_comparecimento_munzona f
            JOIN tb_eleicoes e ON f.cd_eleicao = e.cd_eleicao
            LEFT JOIN tb_municipios m ON f.cd_tse_municipio = m.cd_tse
            WHERE e.ano_eleicao = $1
            GROUP BY f.cd_tse_municipio, m.nm_municipio, m.cd_ibge_7
            ORDER BY nm_municipio;
        """
        try:
            records = await connection.fetch(query, ano)
            return [dict(record) for record in records]
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao buscar comparecimento por município (ano={ano}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError

    @staticmethod
    async def getTotalRs(
        connection: asyncpg.Connection,
        ano: int
    ) -> Optional[Dict[str, Any]]:
        query = """
            SELECT
                SUM(f.qt_aptos)::INT AS qt_aptos,
                SUM(f.qt_comparecimento)::INT AS qt_comparecimento,
                SUM(f.qt_abstencoes)::INT AS qt_abstencoes
            FROM tb_fato_comparecimento_munzona f
            JOIN tb_eleicoes e ON f.cd_eleicao = e.cd_eleicao
            WHERE e.ano_eleicao = $1;
        """
        try:
            record = await connection.fetchrow(query, ano)
            if not record or record["qt_aptos"] is None:
                return None
            return dict(record)
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao buscar total de eleitorado RS (ano={ano}): {dbError}", exc_info=True)
            raise RuntimeError(f"Database query error: {dbError}") from dbError
