import os
import logging
import psycopg2
from psycopg2.extensions import connection as PgConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ETL_Database")


def getDatabaseUrl() -> str:
    """Recupera a URL do banco a partir das variáveis de ambiente."""
    databaseUrl = os.environ.get("DATABASE_URL")
    if not databaseUrl:
        postgresUser = os.environ.get("POSTGRES_USER", "datapoli_user")
        postgresPassword = os.environ.get("POSTGRES_PASSWORD", "datapoli_pass")
        postgresHost = os.environ.get("POSTGRES_HOST", "localhost")
        postgresPort = os.environ.get("POSTGRES_PORT", "5432")
        postgresDb = os.environ.get("POSTGRES_DB", "datapoli_db")
        databaseUrl = f"postgresql://{postgresUser}:{postgresPassword}@{postgresHost}:{postgresPort}/{postgresDb}"
    return databaseUrl


def getPostgresConnection() -> PgConnection:
    """Abre e retorna uma conexão direta com o PostgreSQL com validação rigorosa."""
    connectionString = getDatabaseUrl()
    try:
        pgConn = psycopg2.connect(connectionString)
        pgConn.autocommit = False
        logger.info("Conexão com PostgreSQL estabelecida com sucesso.")
        return pgConn
    except psycopg2.Error as databaseError:
        logger.error(
            f"FALHA CRÍTICA: Não foi possível conectar ao PostgreSQL: {databaseError}",
            exc_info=True
        )
        raise RuntimeError(f"Database connection failure: {databaseError}") from databaseError
