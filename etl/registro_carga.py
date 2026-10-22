import hashlib
import logging
import os
from datetime import datetime
from typing import List, Optional

import psycopg2

from etl.db_connection import getPostgresConnection

logger = logging.getLogger("ETL_RegistroCarga")

TAMANHO_BLOCO_HASH = 1024 * 1024


def calcularSha256(caminhoArquivo: str) -> str:
    """Lê o arquivo em blocos, para não carregar CSVs de centenas de MB inteiros na memória."""
    sha256 = hashlib.sha256()
    with open(caminhoArquivo, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(TAMANHO_BLOCO_HASH), b""):
            sha256.update(bloco)
    return sha256.hexdigest()


def registrarCarga(
    tipo: str,
    ano: int,
    caminhoArquivo: str,
    iniciadoEm: datetime,
    sucesso: bool,
    linhas: Optional[int] = None,
    cdEleicoes: Optional[List[str]] = None,
    erro: Optional[str] = None,
) -> None:
    """Grava uma linha em tb_carga_etl ao fim de cada carga, com sucesso ou falha.

    Nunca derruba a carga: se o registro falhar, só avisa no log."""
    try:
        sha256 = calcularSha256(caminhoArquivo)
        tamanhoBytes = os.path.getsize(caminhoArquivo)
        connection = getPostgresConnection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tb_carga_etl
                        (tipo, ano_eleicao, cd_eleicoes, arquivo_origem, sha256, tamanho_bytes,
                         iniciado_em, status, linhas_carregadas, erro)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        tipo, ano, cdEleicoes or [], os.path.basename(caminhoArquivo), sha256, tamanhoBytes,
                        iniciadoEm, "sucesso" if sucesso else "falha", linhas, erro,
                    ),
                )
            connection.commit()
        finally:
            connection.close()
        logger.info(f"Carga registrada em tb_carga_etl: tipo={tipo} ano={ano} status={'sucesso' if sucesso else 'falha'}")
    except (OSError, psycopg2.Error) as registroErro:
        logger.warning(f"Falha ao registrar carga em tb_carga_etl (a carga não foi afetada): {registroErro}")
