"""Busca de candidato por palavras (reportado pelo operador em 2026-10-24).

A busca exigia o termo como trecho contínuo do nome. "Luciano Zucco" não achava o
governador, cujo nome civil é LUCIANO LORENZINI ZUCCO. Agora cada palavra digitada
precisa aparecer no nome de urna ou no nome civil, em qualquer ordem.

Usa o candidato da semente do conftest (nome civil "Candidato de Teste", urna "CANDIDATO TESTE")
e um candidato próprio, montado como o caso real: nome civil com uma palavra no meio e nome de
urna só com o sobrenome.
"""
import asyncio
import uuid
import asyncpg
import pytest
from app.core.config import settings
from fastapi import Request
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from tests.test_sprint2_endpoints import bearerHeader

BUSCA = "/api/v1/candidatos"
SQ_SEMENTE = 999999001
SQ_NOME_COMPOSTO = 999999002


def _executar(sql: str) -> None:
    async def _rodar():
        connection = await asyncpg.connect(dsn=settings.DATABASE_URL)
        try:
            await connection.execute(sql)
        finally:
            await connection.close()
    asyncio.run(_rodar())


@pytest.fixture(scope="module", autouse=True)
def candidatoComNomeComposto():
    # Como LUCIANO LORENZINI ZUCCO / ZUCCO: "Luciano Revisao" não é trecho contínuo de nenhum dos dois nomes.
    _executar(f"""
        INSERT INTO tb_candidaturas (sq_candidato, cd_eleicao, cd_cargo, nr_candidato,
                                     nm_candidato, nm_urna_candidato, nr_partido, sg_uf)
        VALUES ({SQ_NOME_COMPOSTO}, 'TESTE2022', 6, 13124,
                'LUCIANO LORENZINI REVISAO', 'TENENTE REVISAO', 13, 'RS')
        ON CONFLICT (sq_candidato) DO NOTHING
    """)
    yield
    _executar(f"DELETE FROM tb_candidaturas WHERE sq_candidato = {SQ_NOME_COMPOSTO}")


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def encontrados(client: TestClient, termo: str) -> set:
    resposta = client.get(BUSCA, params={"termo": termo, "ano": 2022, "limite": 200},
                          headers=bearerHeader(str(uuid.uuid4())))
    assert resposta.status_code == 200, resposta.text
    return {item["sq_candidato"] for item in resposta.json()}


def test_palavras_separadas_por_outra_no_nome_civil_sao_encontradas(client: TestClient):
    assert SQ_NOME_COMPOSTO in encontrados(client, "Luciano Revisao")


def test_palavras_podem_vir_uma_do_nome_de_urna_e_outra_do_civil(client: TestClient):
    # "Tenente" só existe no nome de urna; "Luciano", só no nome civil.
    assert SQ_NOME_COMPOSTO in encontrados(client, "Tenente Luciano")


def test_ordem_das_palavras_nao_importa(client: TestClient):
    assert SQ_SEMENTE in encontrados(client, "Teste Candidato")


def test_todas_as_palavras_precisam_aparecer(client: TestClient):
    assert SQ_SEMENTE not in encontrados(client, "Candidato Inexistente")


def test_uma_palavra_continua_funcionando(client: TestClient):
    assert SQ_SEMENTE in encontrados(client, "teste")
