"""Preferências pessoais do usuário, gravadas no servidor (tb_users.preferencias)."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.test_sprint2_endpoints import bearerHeader

PREFERENCIAS = "/api/v1/usuario/preferencias"
PADRAO = {"mapa_padrao": "liderancas", "fontes_legislativas": {"alrs": True, "camara": True, "senado": True}}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as testClient:
        yield testClient


def test_padrao_quando_nada_foi_gravado(client: TestClient):
    headers = bearerHeader(str(uuid.uuid4()), role="operador")
    assert client.get(PREFERENCIAS, headers=headers).json() == PADRAO


def test_grava_e_le_de_volta(client: TestClient):
    headers = bearerHeader(str(uuid.uuid4()), role="operador")
    resposta = client.put(PREFERENCIAS, headers=headers, json={
        "mapa_padrao": "votacao",
        "fontes_legislativas": {"alrs": True, "camara": False, "senado": True},
    })
    assert resposta.status_code == 200
    assert resposta.json()["mapa_padrao"] == "votacao"
    assert client.get(PREFERENCIAS, headers=headers).json()["fontes_legislativas"]["camara"] is False


def test_preferencia_persiste_entre_sessoes(client: TestClient):
    """Persistência no servidor: um novo login (novo token) do mesmo usuário enxerga a mesma preferência."""
    tenant = str(uuid.uuid4())
    client.put(PREFERENCIAS, headers=bearerHeader(tenant, role="operador"), json={"mapa_padrao": "cruzada"})

    novaSessao = bearerHeader(tenant, role="operador")
    assert client.get(PREFERENCIAS, headers=novaSessao).json()["mapa_padrao"] == "cruzada"


def test_atualizacao_parcial_nao_apaga_as_outras_preferencias(client: TestClient):
    headers = bearerHeader(str(uuid.uuid4()), role="operador")
    client.put(PREFERENCIAS, headers=headers, json={"mapa_padrao": "cruzada"})
    client.put(PREFERENCIAS, headers=headers, json={"fontes_legislativas": {"alrs": False, "camara": True, "senado": True}})

    corpo = client.get(PREFERENCIAS, headers=headers).json()
    assert corpo["mapa_padrao"] == "cruzada"
    assert corpo["fontes_legislativas"]["alrs"] is False


def test_preferencias_aparecem_no_me(client: TestClient):
    """O front carrega as preferências no login, junto com o usuário (/auth/me)."""
    headers = bearerHeader(str(uuid.uuid4()), role="operador")
    client.put(PREFERENCIAS, headers=headers, json={"mapa_padrao": "votacao"})

    assert client.get("/api/v1/auth/me", headers=headers).json()["preferencias"]["mapa_padrao"] == "votacao"


def test_valor_desconhecido_e_recusado(client: TestClient):
    headers = bearerHeader(str(uuid.uuid4()), role="operador")
    assert client.put(PREFERENCIAS, headers=headers, json={"mapa_padrao": "satelite"}).status_code == 422
    assert client.put(PREFERENCIAS, headers=headers, json={"campo_inventado": 1}).status_code == 422


def test_fontes_da_preferencia_restringem_a_busca_externa(client: TestClient, monkeypatch):
    """Regressão: o toggle de fontes não era aplicado. Agora a busca só consulta as fontes escolhidas."""
    capturadas = {}

    async def falsa_busca(nome, bases=None, desligadas=()):
        capturadas["desligadas"] = set(desligadas)
        return [], []

    monkeypatch.setattr("app.services.legislative_service.buscar_em_todas_fontes", falsa_busca)
    headers = bearerHeader(str(uuid.uuid4()), role="operador")

    resposta = client.get("/api/v1/gabinete/projetos-lei/buscar-externo",
                          params={"nome": "nadine", "fontes": "alrs"}, headers=headers)

    assert resposta.status_code == 200
    assert {"CAMARA", "SENADO"} <= capturadas["desligadas"]
    assert "ALRS" not in capturadas["desligadas"]


def test_fontes_invalidas_na_busca_sao_recusadas(client: TestClient):
    headers = bearerHeader(str(uuid.uuid4()), role="operador")
    resposta = client.get("/api/v1/gabinete/projetos-lei/buscar-externo",
                          params={"nome": "nadine", "fontes": "alrs,twitter"}, headers=headers)
    assert resposta.status_code == 422
