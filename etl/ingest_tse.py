import os
import time
import zipfile
import logging
import duckdb
import psycopg2
from psycopg2.extras import execute_values
from etl.db_connection import getPostgresConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ETL_DuckDB_TSE")

CSV_FILE_PATH = "votacao_candidato_munzona_2022_RS.csv"
ZIP_FILE_PATH = "votacao.zip"
BATCH_SIZE = 10000


def ensureCsvFileExists() -> str:
    """Verifica se o CSV do TSE existe. Se não existir, extrai do ZIP."""
    if os.path.exists(CSV_FILE_PATH):
        fileSizeMb = os.path.getsize(CSV_FILE_PATH) / (1024 * 1024)
        logger.info(f"Arquivo CSV localizado: {CSV_FILE_PATH} ({fileSizeMb:.2f} MB)")
        return CSV_FILE_PATH

    if os.path.exists(ZIP_FILE_PATH):
        logger.info(f"Extraindo {CSV_FILE_PATH} a partir de {ZIP_FILE_PATH}...")
        try:
            with zipfile.ZipFile(ZIP_FILE_PATH, "r") as zipReference:
                zipReference.extract(CSV_FILE_PATH)
            logger.info("Extração do CSV do TSE concluída com sucesso.")
            return CSV_FILE_PATH
        except (zipfile.BadZipFile, IOError) as zipError:
            logger.error(f"Falha ao extrair arquivo ZIP do TSE: {zipError}", exc_info=True)
            raise RuntimeError(f"Erro de extração ZIP: {zipError}") from zipError

    errorMsg = f"Nenhum arquivo de dados ({CSV_FILE_PATH} ou {ZIP_FILE_PATH}) encontrado no workspace."
    logger.error(errorMsg)
    raise FileNotFoundError(errorMsg)


def executeDuckDbEtl(csvPath: str) -> None:
    """Executa o pipeline colunar com DuckDB e carrega no PostgreSQL de forma idempotente."""
    startTime = time.time()
    logger.info("Iniciando motor colunar DuckDB para processamento analítico do TSE...")

    duckDbConnection = duckdb.connect(":memory:")

    try:
        # 1. Criação de View Virtual sobre o CSV sem carregar tudo em RAM
        logger.info("Mapeando arquivo CSV bruto com DuckDB read_csv...")
        duckDbConnection.execute(f"""
            CREATE VIEW tse_raw AS 
            SELECT * FROM read_csv('{csvPath}', 
                delim=';', 
                header=true, 
                encoding='latin-1', 
                all_varchar=true
            );
        """)
        
        rawRowCount = duckDbConnection.execute("SELECT COUNT(*) FROM tse_raw").fetchone()[0]
        logger.info(f"Total de registros mapeados no CSV bruto do TSE: {rawRowCount:,} linhas.")

        pgConnection = getPostgresConnection()

        with pgConnection.cursor() as pgCursor:
            # 2. Ingestão de tb_eleicoes
            logger.info("Processando e ingerindo Eleições...")
            electionsData = duckDbConnection.execute("""
                SELECT DISTINCT
                    CAST(CD_ELEICAO AS VARCHAR) AS cd_eleicao,
                    CAST(ANO_ELEICAO AS INTEGER) AS ano_eleicao,
                    CAST(NR_TURNO AS INTEGER) AS nr_turno,
                    CAST(TP_ABRANGENCIA AS VARCHAR) AS tp_abrangencia,
                    CAST(DS_ELEICAO AS VARCHAR) AS ds_eleicao,
                    strptime(DT_ELEICAO, '%d/%m/%Y')::DATE AS dt_eleicao
                FROM tse_raw
                WHERE CD_ELEICAO IS NOT NULL;
            """).fetchall()

            insertEleicoesQuery = """
                INSERT INTO tb_eleicoes (cd_eleicao, ano_eleicao, nr_turno, tp_abrangencia, ds_eleicao, dt_eleicao)
                VALUES %s
                ON CONFLICT (cd_eleicao) DO UPDATE SET
                    ds_eleicao = EXCLUDED.ds_eleicao,
                    dt_eleicao = EXCLUDED.dt_eleicao;
            """
            execute_values(pgCursor, insertEleicoesQuery, electionsData)
            logger.info(f"Eleições processadas: {len(electionsData)} registros.")

            # 3. Ingestão de tb_cargos
            logger.info("Processando e ingerindo Cargos Eletivos...")
            cargosData = duckDbConnection.execute("""
                SELECT DISTINCT
                    CAST(CD_CARGO AS INTEGER) AS cd_cargo,
                    CAST(DS_CARGO AS VARCHAR) AS ds_cargo
                FROM tse_raw
                WHERE CD_CARGO IS NOT NULL;
            """).fetchall()

            insertCargosQuery = """
                INSERT INTO tb_cargos (cd_cargo, ds_cargo)
                VALUES %s
                ON CONFLICT (cd_cargo) DO UPDATE SET
                    ds_cargo = EXCLUDED.ds_cargo;
            """
            execute_values(pgCursor, insertCargosQuery, cargosData)
            logger.info(f"Cargos processados: {len(cargosData)} registros.")

            # 4. Ingestão de tb_partidos
            logger.info("Processando e ingerindo Partidos...")
            partidosData = duckDbConnection.execute("""
                SELECT DISTINCT
                    CAST(NR_PARTIDO AS INTEGER) AS nr_partido,
                    CAST(SG_PARTIDO AS VARCHAR) AS sg_partido,
                    CAST(NM_PARTIDO AS VARCHAR) AS nm_partido
                FROM tse_raw
                WHERE NR_PARTIDO IS NOT NULL;
            """).fetchall()

            insertPartidosQuery = """
                INSERT INTO tb_partidos (nr_partido, sg_partido, nm_partido)
                VALUES %s
                ON CONFLICT (nr_partido) DO UPDATE SET
                    sg_partido = EXCLUDED.sg_partido,
                    nm_partido = EXCLUDED.nm_partido;
            """
            execute_values(pgCursor, insertPartidosQuery, partidosData)
            logger.info(f"Partidos processados: {len(partidosData)} registros.")

            # 5. Ingestão de tb_candidaturas (desduplicação estrita por SQ_CANDIDATO)
            logger.info("Processando e ingerindo Candidaturas...")
            candidaturasData = duckDbConnection.execute("""
                SELECT
                    CAST(SQ_CANDIDATO AS BIGINT) AS sq_candidato,
                    CAST(CD_ELEICAO AS VARCHAR) AS cd_eleicao,
                    CAST(CD_CARGO AS INTEGER) AS cd_cargo,
                    CAST(NR_CANDIDATO AS INTEGER) AS nr_candidato,
                    CAST(NM_CANDIDATO AS VARCHAR) AS nm_candidato,
                    CAST(NM_URNA_CANDIDATO AS VARCHAR) AS nm_urna_candidato,
                    CAST(NR_PARTIDO AS INTEGER) AS nr_partido,
                    CAST(SG_UF AS VARCHAR) AS sg_uf,
                    CAST(DS_SITUACAO_CANDIDATURA AS VARCHAR) AS ds_situacao_candidatura,
                    CAST(DS_DETALHE_SITUACAO_CAND AS VARCHAR) AS ds_detalhe_situacao
                FROM tse_raw
                WHERE SQ_CANDIDATO IS NOT NULL
                QUALIFY ROW_NUMBER() OVER (PARTITION BY SQ_CANDIDATO ORDER BY CD_ELEICAO DESC) = 1;
            """).fetchall()

            insertCandidaturasQuery = """
                INSERT INTO tb_candidaturas (
                    sq_candidato, cd_eleicao, cd_cargo, nr_candidato,
                    nm_candidato, nm_urna_candidato, nr_partido, sg_uf,
                    ds_situacao_candidatura, ds_detalhe_situacao
                )
                VALUES %s
                ON CONFLICT (sq_candidato) DO UPDATE SET
                    nm_urna_candidato = EXCLUDED.nm_urna_candidato,
                    ds_situacao_candidatura = EXCLUDED.ds_situacao_candidatura,
                    ds_detalhe_situacao = EXCLUDED.ds_detalhe_situacao;
            """
            execute_values(pgCursor, insertCandidaturasQuery, candidaturasData, page_size=5000)
            logger.info(f"Candidaturas processadas: {len(candidaturasData)} registros.")

            # 6. Atualização dos códigos TSE nos municípios existentes
            logger.info("Correlacionando códigos do TSE com municípios cadastrados...")
            tseMunicipiosMapping = duckDbConnection.execute("""
                SELECT DISTINCT
                    CAST(CD_MUNICIPIO AS VARCHAR) AS cd_tse,
                    UPPER(TRIM(NM_MUNICIPIO)) AS nm_municipio
                FROM tse_raw
                WHERE CD_MUNICIPIO IS NOT NULL;
            """).fetchall()

            for cdTse, nmMun in tseMunicipiosMapping:
                pgCursor.execute("""
                    UPDATE tb_municipios 
                    SET cd_tse = %s 
                    WHERE UPPER(nm_municipio) = %s AND cd_tse IS NULL;
                """, (cdTse, nmMun))

            # 7. Ingestão de Fatos de Votação (Agregação por Município e Zona)
            logger.info("Agregando e inserindo Fatos de Votação Nominal (tb_fato_votacao_munzona)...")
            
            votacaoQuery = """
                SELECT
                    CAST(t.CD_ELEICAO AS VARCHAR) AS cd_eleicao,
                    CAST(t.SQ_CANDIDATO AS BIGINT) AS sq_candidato,
                    CAST(t.CD_MUNICIPIO AS VARCHAR) AS cd_tse_municipio,
                    CAST(t.NR_ZONA AS INTEGER) AS nr_zona,
                    SUM(CAST(t.QT_VOTOS_NOMINAIS AS INTEGER)) AS qt_votos_nominais,
                    SUM(CAST(t.QT_VOTOS_NOMINAIS_VALIDOS AS INTEGER)) AS qt_votos_validos
                FROM tse_raw t
                WHERE t.SQ_CANDIDATO IS NOT NULL
                GROUP BY t.CD_ELEICAO, t.SQ_CANDIDATO, t.CD_MUNICIPIO, t.NR_ZONA;
            """
            
            duckDbCursor = duckDbConnection.cursor()
            duckDbCursor.execute(votacaoQuery)

            insertFatoQuery = """
                INSERT INTO tb_fato_votacao_munzona (
                    cd_eleicao, sq_candidato, cd_tse_municipio,
                    nr_zona, qt_votos_nominais, qt_votos_validos
                )
                VALUES %s
                ON CONFLICT (cd_eleicao, sq_candidato, cd_tse_municipio, nr_zona) DO UPDATE SET
                    qt_votos_nominais = EXCLUDED.qt_votos_nominais,
                    qt_votos_validos = EXCLUDED.qt_votos_validos;
            """

            totalFatos = 0
            while True:
                batch = duckDbCursor.fetchmany(BATCH_SIZE)
                if not batch:
                    break
                execute_values(pgCursor, insertFatoQuery, batch, page_size=BATCH_SIZE)
                totalFatos += len(batch)
                logger.info(f"Fatos de votação inseridos: {totalFatos:,} registros...")

            pgConnection.commit()
            logger.info(f"Total de fatos de votação persistidos com sucesso: {totalFatos:,}")

        pgConnection.close()
        duckDbConnection.close()

        elapsedTime = time.time() - startTime
        logger.info(f"=== PIPELINE DUCKDB FINALIZADO COM SUCESSO EM {elapsedTime:.2f} SEGUNDOS ===")

    except (duckdb.Error, psycopg2.Error, Exception) as pipelineError:
        logger.error(f"FALHA NO PIPELINE ETL DUCKDB: {pipelineError}", exc_info=True)
        raise RuntimeError(f"ETL pipeline failure: {pipelineError}") from pipelineError


def main():
    logger.info("=== INICIANDO PIPELINE ANALÍTICO DE DADOS ELEITORAIS COM DUCKDB ===")
    csvPath = ensureCsvFileExists()
    executeDuckDbEtl(csvPath)


if __name__ == "__main__":
    main()
