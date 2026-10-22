"""Enfileira uma carga em tb_job_etl para o worker consumir.

Uso: python -m etl.enfileirar_carga <votacao|comparecimento> <ano>

Usado pelo pipeline de deploy para popular o banco na carga inicial. O índice único parcial
de tb_job_etl permite só um job ativo por vez: com outro pendente ou em execução, falha em vez de duplicar.
"""
import logging
import sys

from psycopg2.errors import UniqueViolation

from etl.db_connection import getPostgresConnection

logger = logging.getLogger("ETL_Enfileirar")

TIPOS_VALIDOS = ("votacao", "comparecimento")


def enfileirarCarga(tipo: str, ano: int, solicitadoPor: str) -> int:
    connection = getPostgresConnection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tb_job_etl (tipo, ano_eleicao, status, solicitado_por)
                VALUES (%s, %s, 'pendente', %s)
                RETURNING id_job;
                """,
                (tipo, ano, solicitadoPor),
            )
            idJob = cursor.fetchone()[0]
        connection.commit()
        return idJob
    finally:
        connection.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    if len(sys.argv) != 3 or sys.argv[1] not in TIPOS_VALIDOS:
        sys.exit(f"Uso: python -m etl.enfileirar_carga <{'|'.join(TIPOS_VALIDOS)}> <ano>")

    tipo, ano = sys.argv[1], int(sys.argv[2])
    try:
        idJob = enfileirarCarga(tipo, ano, "pipeline-deploy")
    except UniqueViolation:
        sys.exit("Já existe uma carga pendente ou em execução. Aguarde ela terminar.")
    logger.info(f"Carga {tipo} {ano} enfileirada (job {idJob})")


if __name__ == "__main__":
    main()
