"""Fila de jobs de carga em tb_job_etl (Postgres). Um job ativo por vez, garantido pelo índice único parcial."""
import logging
from typing import Optional

import psycopg2

from etl.db_connection import getPostgresConnection

logger = logging.getLogger("ETL_Jobs")


def reivindicarProximo() -> Optional[dict]:
    """Marca o job pendente mais antigo como 'executando'. SKIP LOCKED evita dois workers pegarem o mesmo job."""
    connection = getPostgresConnection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE tb_job_etl
                   SET status = 'executando', iniciado_em = NOW()
                 WHERE id_job = (
                       SELECT id_job FROM tb_job_etl
                        WHERE status = 'pendente'
                        ORDER BY solicitado_em
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED)
             RETURNING id_job, tipo, ano_eleicao;
            """)
            linha = cursor.fetchone()
        connection.commit()
        if linha is None:
            return None
        return {"id_job": linha[0], "tipo": linha[1], "ano_eleicao": linha[2]}
    finally:
        connection.close()


def concluirJob(idJob: int, sucesso: bool, erro: Optional[str] = None) -> None:
    connection = getPostgresConnection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tb_job_etl
                   SET status = %s, concluido_em = NOW(), erro = %s
                 WHERE id_job = %s;
                """,
                ("concluido" if sucesso else "falha", erro, idJob),
            )
        connection.commit()
    finally:
        connection.close()


def encerrarJobsOrfaos() -> int:
    """Ao subir, um job 'executando' é órfão: o worker anterior morreu no meio. Marca como falha para liberar a fila."""
    connection = getPostgresConnection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE tb_job_etl
                   SET status = 'falha', concluido_em = NOW(),
                       erro = 'interrompido: worker reiniciado durante a execução'
                 WHERE status = 'executando';
            """)
            afetados = cursor.rowcount
        connection.commit()
        return afetados
    finally:
        connection.close()
