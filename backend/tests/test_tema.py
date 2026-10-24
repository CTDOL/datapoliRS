"""Cores do gabinete (ADR 038): só o admin do gabinete altera, com contraste mínimo AA."""
import uuid

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from app.services.tema_service import contraste_com_branco
from tests.test_sprint2_endpoints import bearerHeader

TEMA = "/api/v1/gabinete/tema"


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def test_contraste_aceita_roxo_e_recusa_amarelo():
    assert contraste_com_branco("#9333ea") >= 4.5
    assert contraste_com_branco("#fbbf24") < 4.5


def test_admin_define_cor_valida(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    resposta = client.put(TEMA, headers=headers, json={"cor_primaria": "#1d4ed8", "cor_secundaria": None})

    assert resposta.status_code == 200
    assert resposta.json()["cor_primaria"] == "#1d4ed8"
    assert client.get(TEMA, headers=headers).json()["cor_primaria"] == "#1d4ed8"


def test_cor_com_contraste_insuficiente_e_recusada(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    resposta = client.put(TEMA, headers=headers, json={"cor_primaria": "#fbbf24"})

    assert resposta.status_code == 422
    assert "contraste" in resposta.json()["detail"]


def test_formato_invalido_e_recusado(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")

    assert client.put(TEMA, headers=headers, json={"cor_primaria": "roxo"}).status_code == 422


def test_operador_nao_altera_as_cores(client):
    headers = bearerHeader(str(uuid.uuid4()), role="operador")

    assert client.put(TEMA, headers=headers, json={"cor_primaria": "#1d4ed8"}).status_code == 403


def test_me_devolve_as_cores_do_gabinete(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    client.put(TEMA, headers=headers, json={"cor_primaria": "#0e7490"})

    corpo = client.get("/api/v1/auth/me", headers=headers).json()

    assert corpo["cor_primaria"] == "#0e7490"


def test_tema_padrao_e_escuro(client):
    """Gabinete sem escolha salva continua escuro: a aparência atual não muda para quem já usa o sistema."""
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    assert client.get(TEMA, headers=headers).json()["tp_tema"] == "escuro"


def test_admin_troca_para_claro_e_de_volta(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    resposta = client.put(TEMA, headers=headers, json={"tp_tema": "claro"})
    assert resposta.status_code == 200
    assert resposta.json()["tp_tema"] == "claro"
    assert client.get(TEMA, headers=headers).json()["tp_tema"] == "claro"

    client.put(TEMA, headers=headers, json={"tp_tema": "escuro"})
    assert client.get(TEMA, headers=headers).json()["tp_tema"] == "escuro"


def test_salvar_cores_sem_tp_tema_mantem_o_tema(client):
    """Regressão: salvar só as cores não pode reverter o tema escolhido (COALESCE em tp_tema)."""
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    client.put(TEMA, headers=headers, json={"tp_tema": "claro"})
    client.put(TEMA, headers=headers, json={"cor_primaria": "#1d4ed8", "cor_secundaria": None})
    assert client.get(TEMA, headers=headers).json()["tp_tema"] == "claro"


def test_tema_desconhecido_e_recusado(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    resposta = client.put(TEMA, headers=headers, json={"tp_tema": "azul"})
    assert resposta.status_code == 422


def test_operador_nao_troca_o_tema(client):
    headers = bearerHeader(str(uuid.uuid4()), role="operador")
    resposta = client.put(TEMA, headers=headers, json={"tp_tema": "claro"})
    assert resposta.status_code == 403
