import os
import time
import zipfile
import logging
import argparse
import duckdb
import psycopg2
from psycopg2.extras import execute_values
from etl.db_connection import getPostgresConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ETL_DuckDB_Comparecimento")

DATA_DIR = os.path.join("etl", "data")
BATCH_SIZE = 10000


def ensureCsvFileExists(ano: int) -> str:
    """Verifica se o CSV de detalhe_votacao_munzona do ano informado existe. Se não
    existir, extrai do ZIP correspondente.

    O TSE publica um ZIP nacional por ano (detalhe_votacao_munzona_{ano}.zip)
    contendo um CSV por UF, com os totais de eleitorado apto, comparecimento
    e abstenções por município/zona — dataset independente de
    votacao_candidato_munzona, que só traz votos nominais por candidato.
    """
    csvFileName = f"detalhe_votacao_munzona_{ano}_RS.csv"
    csvFilePath = os.path.join(DATA_DIR, csvFileName)
    zipFilePath = os.path.join(DATA_DIR, f"detalhe_votacao_munzona_{ano}.zip")

    if os.path.exists(csvFilePath):
        fileSizeMb = os.path.getsize(csvFilePath) / (1024 * 1024)
        logger.info(f"Arquivo CSV localizado: {csvFilePath} ({fileSizeMb:.2f} MB)")
        return csvFilePath

    if os.path.exists(zipFilePath):
        logger.info(f"Extraindo {csvFileName} a partir de {zipFilePath}...")
        try:
            with zipfile.ZipFile(zipFilePath, "r") as zipReference:
                zipReference.extract(csvFileName, path=DATA_DIR)
            logger.info("Extração do CSV de comparecimento concluída com sucesso.")
            return csvFilePath
        except (zipfile.BadZipFile, IOError) as zipError:
            logger.error(f"Falha ao extrair arquivo ZIP do TSE: {zipError}", exc_info=True)
            raise RuntimeError(f"Erro de extração ZIP: {zipError}") from zipError

    errorMsg = (
        f"Nenhum arquivo de dados encontrado para o ano {ano} "
        f"({csvFilePath} ou {zipFilePath}). Baixe o ZIP de "
        f"https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_munzona/"
        f"detalhe_votacao_munzona_{ano}.zip e salve como {zipFilePath}. "
        f"(Nota: o domínio do TSE bloqueia downloads automatizados via curl/script "
        f"por fingerprint de TLS — baixe manualmente pelo navegador.)"
    )
    logger.error(errorMsg)
    raise FileNotFoundError(errorMsg)


def executeDuckDbEtl(csvPath: str) -> None:
    """Executa o pipeline colunar com DuckDB e carrega no PostgreSQL de forma idempotente."""
    startTime = time.time()
    logger.info("Iniciando motor colunar DuckDB para eleitorado/comparecimento...")

    duckDbConnection = duckdb.connect(":memory:")

    try:
        logger.info("Mapeando arquivo CSV bruto com DuckDB read_csv...")
        duckDbConnection.execute(f"""
            CREATE VIEW comparecimento_raw AS
            SELECT * FROM read_csv('{csvPath}',
                delim=';',
                header=true,
                encoding='latin-1',
                all_varchar=true
            );
        """)

        rawRowCount = duckDbConnection.execute("SELECT COUNT(*) FROM comparecimento_raw").fetchone()[0]
        logger.info(f"Total de registros mapeados no CSV bruto: {rawRowCount:,} linhas.")

        pgConnection = getPostgresConnection()

        with pgConnection.cursor() as pgCursor:
            logger.info("Agregando e inserindo fatos de comparecimento (tb_fato_comparecimento_munzona)...")

            # QT_APTOS/QT_COMPARECIMENTO/QT_ABSTENCOES se repetem por linha de
            # CD_CARGO no CSV bruto (mesmo eleitorado físico votando em todos os
            # cargos do mesmo turno) — por isso MAX() ao agrupar por zona, nunca
            # SUM(), senão o valor seria multiplicado pela quantidade de cargos.
            comparecimentoQuery = """
                SELECT
                    CAST(t.CD_ELEICAO AS VARCHAR) AS cd_eleicao,
                    CAST(t.CD_MUNICIPIO AS VARCHAR) AS cd_tse_municipio,
                    CAST(t.NR_ZONA AS INTEGER) AS nr_zona,
                    MAX(CAST(t.NM_MUNICIPIO AS VARCHAR)) AS nm_municipio_tse,
                    MAX(CAST(t.QT_APTOS AS INTEGER)) AS qt_aptos,
                    MAX(CAST(t.QT_COMPARECIMENTO AS INTEGER)) AS qt_comparecimento,
                    MAX(CAST(t.QT_ABSTENCOES AS INTEGER)) AS qt_abstencoes
                FROM comparecimento_raw t
                WHERE t.CD_MUNICIPIO IS NOT NULL
                GROUP BY t.CD_ELEICAO, t.CD_MUNICIPIO, t.NR_ZONA;
            """

            duckDbCursor = duckDbConnection.cursor()
            duckDbCursor.execute(comparecimentoQuery)

            insertQuery = """
                INSERT INTO tb_fato_comparecimento_munzona (
                    cd_eleicao, cd_tse_municipio, nr_zona,
                    nm_municipio_tse, qt_aptos, qt_comparecimento, qt_abstencoes
                )
                VALUES %s
                ON CONFLICT (cd_eleicao, cd_tse_municipio, nr_zona) DO UPDATE SET
                    nm_municipio_tse = EXCLUDED.nm_municipio_tse,
                    qt_aptos = EXCLUDED.qt_aptos,
                    qt_comparecimento = EXCLUDED.qt_comparecimento,
                    qt_abstencoes = EXCLUDED.qt_abstencoes;
            """

            totalFatos = 0
            while True:
                batch = duckDbCursor.fetchmany(BATCH_SIZE)
                if not batch:
                    break
                execute_values(pgCursor, insertQuery, batch, page_size=BATCH_SIZE)
                totalFatos += len(batch)
                logger.info(f"Fatos de comparecimento inseridos: {totalFatos:,} registros...")

            pgConnection.commit()
            logger.info(f"Total de fatos de comparecimento persistidos com sucesso: {totalFatos:,}")

        pgConnection.close()
        duckDbConnection.close()

        elapsedTime = time.time() - startTime
        logger.info(f"=== PIPELINE DUCKDB FINALIZADO COM SUCESSO EM {elapsedTime:.2f} SEGUNDOS ===")

    except (duckdb.Error, psycopg2.Error, Exception) as pipelineError:
        logger.error(f"FALHA NO PIPELINE ETL DUCKDB: {pipelineError}", exc_info=True)
        raise RuntimeError(f"ETL pipeline failure: {pipelineError}") from pipelineError


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ETL de eleitorado apto, comparecimento e abstenções do TSE (por município/zona) para o RS, via DuckDB."
    )
    parser.add_argument(
        "--ano",
        type=int,
        required=True,
        help="Ano do pleito a processar (ex.: 2022, 2026). Sem valor padrão: "
             "o resultado só existe depois da apuração do respectivo ano.",
    )
    return parser.parse_args()


def main():
    args = parseArgs()
    logger.info(f"=== INICIANDO PIPELINE DE ELEITORADO/COMPARECIMENTO COM DUCKDB (ano={args.ano}) ===")
    csvPath = ensureCsvFileExists(args.ano)
    executeDuckDbEtl(csvPath)


if __name__ == "__main__":
    main()
