import asyncio

import asyncpg
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

# Número eleitoral usado só por este módulo. Não é 13123, para não alterar o cenário
# de test_sprint2_endpoints.py. A fixture insere e remove tudo que cria.
NUMERO_AMBIGUO = 77777
SQ_CARGO_6_COM_VOTOS = 999999101
SQ_CARGO_7_SEM_VOTOS = 999999102


async def _inserir_dados():
    connection = await asyncpg.connect(dsn=settings.DATABASE_URL)
    try:
        await connection.execute(
            """
            INSERT INTO tb_cargos (cd_cargo, ds_cargo) VALUES (7, 'Deputado Estadual')
            ON CONFLICT (cd_cargo) DO NOTHING
            """
        )
        await connection.execute(
            """
            INSERT INTO tb_candidaturas (
                sq_candidato, cd_eleicao, cd_cargo, nr_candidato,
                nm_candidato, nm_urna_candidato, nr_partido, sg_uf
            ) VALUES
                ($1, 'TESTE2022', 6, $3, 'Cand. Federal Ambigua', 'FED AMBIGUA', 13, 'RS'),
                ($2, 'TESTE2022', 7, $3, 'Cand. Estadual Ambigua', 'EST AMBIGUA', 13, 'RS')
            ON CONFLICT (sq_candidato) DO NOTHING
            """,
            SQ_CARGO_6_COM_VOTOS, SQ_CARGO_7_SEM_VOTOS, NUMERO_AMBIGUO,
        )
        await connection.execute(
            """
            INSERT INTO tb_fato_votacao_munzona (
                cd_eleicao, sq_candidato, cd_tse_municipio, cd_ibge_7,
                nr_zona, qt_votos_nominais, qt_votos_validos
            ) VALUES ('TESTE2022', $1, '43169', '4314902', 2, 50, 50)
            ON CONFLICT (cd_eleicao, sq_candidato, cd_tse_municipio, nr_zona) DO NOTHING
            """,
            SQ_CARGO_6_COM_VOTOS,
        )
    finally:
        await connection.close()


async def _remover_dados():
    connection = await asyncpg.connect(dsn=settings.DATABASE_URL)
    try:
        await connection.execute(
            "DELETE FROM tb_fato_votacao_munzona WHERE sq_candidato = ANY($1::bigint[])",
            [SQ_CARGO_6_COM_VOTOS, SQ_CARGO_7_SEM_VOTOS],
        )
        await connection.execute(
            "DELETE FROM tb_candidaturas WHERE sq_candidato = ANY($1::bigint[])",
            [SQ_CARGO_6_COM_VOTOS, SQ_CARGO_7_SEM_VOTOS],
        )
    finally:
        await connection.close()


@pytest.fixture(scope="module")
def numero_ambiguo():
    asyncio.run(_inserir_dados())
    yield NUMERO_AMBIGUO
    asyncio.run(_remover_dados())


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as testClient:
        yield testClient


def test_rota_legada_com_numero_em_dois_cargos_devolve_o_registro_de_maior_sq(client: TestClient, numero_ambiguo: int):
    """CARACTERIZAÇÃO — congela o comportamento ATUAL, que é provavelmente errado.

    A rota legada não recebe cargo. Com o número 77777 existindo em Deputado Federal
    (SQ 999999101, 50 votos) e em Deputado Estadual (SQ 999999102, sem votos), o
    desempate por `ORDER BY sq_candidato DESC` escolhe o SQ 999999102 e devolve lista vazia.
    Não é regra de negócio. Decisão registrada no Diário 017: parametrizar o cargo
    depois, com aviso de depreciação. Ao mudar isto, atualizar este teste no mesmo commit.
    """
    resposta = client.get(f"/api/v1/candidatas/{numero_ambiguo}/votos")
    assert resposta.status_code == 200
    assert resposta.json() == []
