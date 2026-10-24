import json
from typing import Any, Dict, List, Optional

import asyncpg


class ManutencaoRepository:
    """Leitura da saúde dos dados eleitorais e do histórico de cargas (tb_carga_etl)."""

    async def saudePorPleito(self, connection: asyncpg.Connection) -> List[Dict[str, Any]]:
        query = """
            SELECT
                e.cd_eleicao,
                e.ano_eleicao,
                e.ds_eleicao,
                e.nr_turno,
                (SELECT count(*) FROM tb_fato_votacao_munzona v
                  WHERE v.cd_eleicao = e.cd_eleicao) AS linhas_votacao,
                (SELECT count(DISTINCT v.cd_tse_municipio) FROM tb_fato_votacao_munzona v
                  WHERE v.cd_eleicao = e.cd_eleicao) AS municipios_votacao,
                (SELECT count(DISTINCT v.nr_zona) FROM tb_fato_votacao_munzona v
                  WHERE v.cd_eleicao = e.cd_eleicao) AS zonas_votacao,
                (SELECT count(DISTINCT v.cd_tse_municipio) FROM tb_fato_votacao_munzona v
                  WHERE v.cd_eleicao = e.cd_eleicao
                    AND NOT EXISTS (SELECT 1 FROM tb_municipios m
                                    WHERE m.cd_tse = v.cd_tse_municipio)) AS codigos_sem_cadastro,
                (SELECT count(*) FROM tb_fato_comparecimento_munzona c
                  WHERE c.cd_eleicao = e.cd_eleicao) AS linhas_comparecimento
            FROM tb_eleicoes e
            ORDER BY e.ano_eleicao DESC, e.cd_eleicao;
        """
        records = await connection.fetch(query)
        return [dict(record) for record in records]

    async def listarCargas(self, connection: asyncpg.Connection, limite: int) -> List[Dict[str, Any]]:
        query = """
            SELECT id_carga, tipo, ano_eleicao, cd_eleicoes, arquivo_origem, sha256,
                   tamanho_bytes, iniciado_em, concluido_em, status, linhas_carregadas,
                   erro, operador
            FROM tb_carga_etl
            ORDER BY concluido_em DESC, id_carga DESC
            LIMIT $1;
        """
        records = await connection.fetch(query, limite)
        return [dict(record) for record in records]

    async def criarJob(self, connection: asyncpg.Connection, tipo: str, ano: int, solicitadoPor: str) -> Dict[str, Any]:
        """Enfileira uma carga. Levanta UniqueViolationError se já houver um job ativo (índice único parcial)."""
        record = await connection.fetchrow(
            """
            INSERT INTO tb_job_etl (tipo, ano_eleicao, status, solicitado_por)
            VALUES ($1, $2, 'pendente', $3)
            RETURNING id_job, tipo, ano_eleicao, status, solicitado_por, solicitado_em,
                      iniciado_em, concluido_em, erro;
            """,
            tipo, ano, solicitadoPor,
        )
        return dict(record)

    async def listarJobs(self, connection: asyncpg.Connection, limite: int) -> List[Dict[str, Any]]:
        records = await connection.fetch(
            """
            SELECT id_job, tipo, ano_eleicao, status, solicitado_por, solicitado_em,
                   iniciado_em, concluido_em, erro
            FROM tb_job_etl
            ORDER BY solicitado_em DESC, id_job DESC
            LIMIT $1;
            """,
            limite,
        )
        return [dict(record) for record in records]


    async def pleito(self, connection: asyncpg.Connection, cdEleicao: str) -> Optional[Dict[str, Any]]:
        record = await connection.fetchrow(
            "SELECT cd_eleicao, ano_eleicao, ds_eleicao FROM tb_eleicoes WHERE cd_eleicao = $1;",
            cdEleicao,
        )
        return dict(record) if record else None

    async def existeCargaOkDeVotacao(self, connection: asyncpg.Connection, cdEleicao: str, ano: int) -> bool:
        return await connection.fetchval(
            """
            SELECT EXISTS (
                SELECT 1 FROM tb_carga_etl
                 WHERE tipo = 'votacao' AND status = 'sucesso'
                   AND ano_eleicao = $1 AND $2 = ANY(cd_eleicoes));
            """,
            ano, cdEleicao,
        )

    async def registrarAuditoria(self, connection: asyncpg.Connection, acao: str, detalhe: Dict[str, Any], operador: str) -> None:
        await connection.execute(
            "INSERT INTO tb_auditoria_manutencao (acao, detalhe, operador) VALUES ($1, $2::jsonb, $3);",
            acao, json.dumps(detalhe), operador,
        )
