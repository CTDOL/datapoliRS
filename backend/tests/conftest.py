import asyncio
import atexit
import os
import shutil
import tempfile

# Redis próprio dos testes, definido antes de carregar a configuração. O banco 0 é o do dev e
# do hml: o cache "system:config:all" dos testes (lido do datapoli_test, ano 2022) vazava para
# as telas do dev e do hml por até 60 s, e contadores do limitador se misturavam (2026-10-24).
os.environ["REDIS_URL"] = os.environ.get("REDIS_URL_TESTES", "redis://localhost:6379/15")

# Fotos de liderança dos testes vão para um diretório temporário. A pasta padrão é a do dev, que o hml
# também monta, porque os dois usam o mesmo banco (ADR 043 §4). Sem isso, os testes gravam nela.
pastaUploadsTeste = tempfile.mkdtemp(prefix="datapoli_uploads_teste_")
os.environ["UPLOADS_DIR"] = pastaUploadsTeste
atexit.register(shutil.rmtree, pastaUploadsTeste, True)

import asyncpg  # noqa: E402
import pytest  # noqa: E402
from app.core.config import settings  # noqa: E402


def pytest_sessionstart(session):
    """Os testes criam gabinetes, usuários e dados de referência. Fora da CI (que usa um
    banco efêmero), recusa rodar no datapoli_db, que é o banco da demonstração.
    Use `make test`, que aponta para datapoli_test."""
    apontaParaDemo = settings.DATABASE_URL.endswith("/datapoli_db")
    if apontaParaDemo and os.environ.get("CI") != "true":
        pytest.exit(
            "Recusado: os testes apontam para datapoli_db (banco da demonstração). Use `make test`.",
            returncode=3,
        )


@pytest.fixture(scope="session", autouse=True)
def seed_dados_referencia():
    """Semente mínima de dados de referência (eleição, município, partido, cargo,
    candidatura e um fato de votação) para os testes que dependem de dados reais
    do TSE/PostGIS existirem no banco — normalmente carregados via ETL manual
    (etl/import_municipios_geojson.py, scripts/processar_votos.py), que não roda
    em CI. Idempotente (ON CONFLICT DO NOTHING) para rodar seguro em qualquer banco."""
    async def _seed():
        connection = await asyncpg.connect(dsn=settings.DATABASE_URL)
        try:
            await connection.execute(
                """
                INSERT INTO tb_eleicoes (cd_eleicao, ano_eleicao, nr_turno, tp_abrangencia, ds_eleicao, dt_eleicao)
                VALUES ('TESTE2022', 2022, 1, 'E', 'Eleição de Teste', '2022-10-02')
                ON CONFLICT (cd_eleicao) DO NOTHING
                """
            )
            await connection.execute(
                """
                INSERT INTO tb_municipios (cd_ibge_7, cd_tse, nm_municipio, sg_uf, geometria)
                VALUES (
                    '4314902', '43169', 'Porto Alegre', 'RS',
                    ST_GeomFromText('MULTIPOLYGON(((-51.23 -30.03, -51.22 -30.03, -51.22 -30.02, -51.23 -30.02, -51.23 -30.03)))', 4326)
                )
                ON CONFLICT (cd_ibge_7) DO NOTHING
                """
            )
            await connection.execute(
                """
                INSERT INTO tb_partidos (nr_partido, sg_partido, nm_partido)
                VALUES (13, 'PT-TESTE', 'Partido de Teste')
                ON CONFLICT (nr_partido) DO NOTHING
                """
            )
            await connection.execute(
                """
                INSERT INTO tb_cargos (cd_cargo, ds_cargo)
                VALUES (6, 'Deputado Federal')
                ON CONFLICT (cd_cargo) DO NOTHING
                """
            )
            await connection.execute(
                """
                INSERT INTO tb_candidaturas (
                    sq_candidato, cd_eleicao, cd_cargo, nr_candidato,
                    nm_candidato, nm_urna_candidato, nr_partido, sg_uf
                )
                VALUES (999999001, 'TESTE2022', 6, 13123, 'Candidato de Teste', 'CANDIDATO TESTE', 13, 'RS')
                ON CONFLICT (sq_candidato) DO NOTHING
                """
            )
            await connection.execute(
                """
                INSERT INTO tb_fato_votacao_munzona (
                    cd_eleicao, sq_candidato, cd_tse_municipio, cd_ibge_7,
                    nr_zona, qt_votos_nominais, qt_votos_validos
                )
                VALUES ('TESTE2022', 999999001, '43169', '4314902', 1, 100, 100)
                ON CONFLICT (cd_eleicao, sq_candidato, cd_tse_municipio, nr_zona) DO NOTHING
                """
            )
        finally:
            await connection.close()
    asyncio.run(_seed())
