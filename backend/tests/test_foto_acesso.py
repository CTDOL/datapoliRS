"""Acesso às fotos de lideranças (revisão de 2026-10-24, achado M2).

As fotos eram servidas por StaticFiles em /uploads, sem login e sem conferência de gabinete.
Quem tivesse o link via a foto para sempre. A URL gravada no banco continua a mesma; quem
responde agora é uma rota que exige sessão e confere se a liderança é do gabinete.
"""
import uuid
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from tests.test_foto_sanitizacao import jpegComGps, criarLideranca, enviarFoto
from tests.test_sprint2_endpoints import bearerHeader


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


@pytest.fixture(scope="module")
def foto(client: TestClient):
    tenant = str(uuid.uuid4())
    idLideranca = criarLideranca(client, tenant)
    resposta = enviarFoto(client, tenant, idLideranca, jpegComGps())
    assert resposta.status_code == 200
    yield {"tenant": tenant, "url": resposta.json()["ds_foto_url"]}
    client.delete(f"/api/v1/gabinete/liderancas/{idLideranca}", headers=bearerHeader(tenant))


def test_foto_sem_login_e_recusada(client: TestClient, foto):
    client.cookies.clear()
    assert client.get(foto["url"]).status_code == 401


def test_foto_de_outro_gabinete_nao_e_entregue(client: TestClient, foto):
    assert client.get(foto["url"], headers=bearerHeader(str(uuid.uuid4()))).status_code == 404


def test_conta_da_plataforma_nao_ve_foto_de_gabinete(client: TestClient, foto):
    plataforma = bearerHeader(str(uuid.uuid4()), role="super_admin")
    assert client.get(foto["url"], headers=plataforma).status_code == 403


def test_gabinete_dono_recebe_a_foto(client: TestClient, foto):
    resposta = client.get(foto["url"], headers=bearerHeader(foto["tenant"]))
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "image/jpeg"
    assert "private" in resposta.headers.get("cache-control", "")


@pytest.mark.parametrize("arquivo", ["..%2F..%2Fmain.py", "main.py", "nao-e-uuid.jpg"])
def test_nome_fora_do_padrao_nao_e_servido(client: TestClient, foto, arquivo):
    resposta = client.get(f"/uploads/liderancas/{arquivo}", headers=bearerHeader(foto["tenant"]))
    assert resposta.status_code == 404
