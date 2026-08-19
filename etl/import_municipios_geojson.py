import os
import json
import logging
import psycopg2
from etl.db_connection import getPostgresConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ETL_Municipios_GeoJSON")

GEOJSON_FILE_PATH = os.path.join("app", "static", "rs_municipios.json")


def loadMunicipiosGeoJson(filePath: str) -> dict:
    """Lê o arquivo GeoJSON dos municípios do Rio Grande do Sul."""
    if not os.path.exists(filePath):
        errorMsg = f"Arquivo GeoJSON não encontrado no caminho: {filePath}"
        logger.error(errorMsg)
        raise FileNotFoundError(errorMsg)

    try:
        with open(filePath, "r", encoding="utf-8") as fileDescriptor:
            geoJsonData = json.load(fileDescriptor)
            logger.info(f"Arquivo GeoJSON carregado com sucesso: {filePath}")
            return geoJsonData
    except json.JSONDecodeError as jsonError:
        logger.error(f"Erro ao parsear GeoJSON ({filePath}): {jsonError}", exc_info=True)
        raise
    except IOError as ioError:
        logger.error(f"Erro de I/O ao ler {filePath}: {ioError}", exc_info=True)
        raise


def insertMunicipiosSpatialData(geoJsonPayload: dict) -> int:
    """Insere ou atualiza os municípios e suas geometrias PostGIS de forma idempotente."""
    featuresList = geoJsonPayload.get("features", [])
    totalFeatures = len(featuresList)
    logger.info(f"Iniciando ingestão de {totalFeatures} municípios no banco de dados PostGIS...")

    insertQuery = """
        INSERT INTO tb_municipios (cd_ibge_7, nm_municipio, sg_uf, geometria)
        VALUES (
            %(cd_ibge_7)s,
            %(nm_municipio)s,
            'RS',
            ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%(geom_json)s), 4326))
        )
        ON CONFLICT (cd_ibge_7) DO UPDATE SET
            nm_municipio = EXCLUDED.nm_municipio,
            geometria = EXCLUDED.geometria;
    """

    pgConnection = getPostgresConnection()
    insertedCount = 0

    try:
        with pgConnection.cursor() as cursor:
            for feature in featuresList:
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})

                ibgeCode = str(properties.get("id", "")).strip()
                municipioName = str(properties.get("name", "")).strip()
                geomJsonString = json.dumps(geometry)

                if not ibgeCode or not municipioName or not geometry:
                    logger.warning(f"Feição inválida ignorada: ID={ibgeCode}, Nome={municipioName}")
                    continue

                cursor.execute(
                    insertQuery,
                    {
                        "cd_ibge_7": ibgeCode,
                        "nm_municipio": municipioName,
                        "geom_json": geomJsonString,
                    }
                )
                insertedCount += 1

            pgConnection.commit()
            logger.info(f"Ingestão concluída com sucesso! Total de municípios inseridos/atualizados: {insertedCount}/{totalFeatures}")
            return insertedCount

    except psycopg2.Error as databaseError:
        pgConnection.rollback()
        logger.error(f"Erro durante a transação de inserção espacial: {databaseError}", exc_info=True)
        raise RuntimeError(f"Falha na carga espacial de municípios: {databaseError}") from databaseError
    finally:
        pgConnection.close()


def main():
    logger.info("=== INICIANDO PIPELINE DE INGESTÃO ESPACIAL DE MUNICÍPIOS ===")
    geoJsonData = loadMunicipiosGeoJson(GEOJSON_FILE_PATH)
    totalImported = insertMunicipiosSpatialData(geoJsonData)
    logger.info(f"=== PIPELINE ESPACIAL FINALIZADO COM SUCESSO. TOTAL: {totalImported} ===")


if __name__ == "__main__":
    main()
