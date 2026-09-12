import asyncio
import asyncpg
import pytest
from app.core.config import settings


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
