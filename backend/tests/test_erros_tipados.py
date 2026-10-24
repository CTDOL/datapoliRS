"""Erros do banco chegam tipados aos handlers (revisão de 2026-10-24, achado B1).

Os repositórios de gabinete embrulhavam todo asyncpg.PostgresError em RuntimeError. Com isso,
os handlers de violação de FK (422) e de unicidade (409) de app/core/exceptions.py nunca
eram acionados, e o usuário recebia o 500 genérico ("erro catastrófico"). Foi a causa raiz
do achado A3. Município inexistente é o caso mais simples de alcançar pela API: o serviço
não valida o código antes de gravar, e quem barra é a FK com tb_municipios.
"""
import uuid
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from tests.test_sprint2_endpoints import bearerHeader

MUNICIPIO_INEXISTENTE = "0000000"
PORTO_ALEGRE = "4314902"


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        # raise_server_exceptions=False: um 500 precisa virar resposta, não exceção no teste.
        with TestClient(app, raise_server_exceptions=False) as testClient:
            yield testClient


def assertReferenciaInexistente(resposta) -> None:
    assert resposta.status_code == 422, resposta.text
    assert resposta.json()["title"] == "Violação de Referência"


def test_lideranca_com_municipio_inexistente_responde_422(client: TestClient):
    resposta = client.post("/api/v1/gabinete/liderancas", headers=bearerHeader(str(uuid.uuid4())),
                           json={"nm_completo": "Liderança com município errado", "municipios": [MUNICIPIO_INEXISTENTE]})
    assertReferenciaInexistente(resposta)


def test_alterar_lideranca_para_municipio_inexistente_responde_422(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)
    criada = client.post("/api/v1/gabinete/liderancas", headers=headers,
                         json={"nm_completo": "Liderança válida", "municipios": [PORTO_ALEGRE]})
    assert criada.status_code == 201, criada.text
    idLideranca = criada.json()["id_lideranca"]

    resposta = client.put(f"/api/v1/gabinete/liderancas/{idLideranca}", headers=headers,
                          json={"municipios": [MUNICIPIO_INEXISTENTE]})

    assertReferenciaInexistente(resposta)
    client.delete(f"/api/v1/gabinete/liderancas/{idLideranca}", headers=headers)


def test_emenda_com_municipio_inexistente_responde_422(client: TestClient):
    resposta = client.post("/api/v1/gabinete/emendas", headers=bearerHeader(str(uuid.uuid4())), json={
        "ano_exercicio": 2026, "ds_objeto": "Emenda com município errado",
        "vl_indicado": "1000", "cd_ibge_7": MUNICIPIO_INEXISTENTE})
    assertReferenciaInexistente(resposta)
