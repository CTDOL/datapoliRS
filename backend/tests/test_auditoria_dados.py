"""Trilha de operações sobre dados pessoais (revisão de 2026-10-24, achado M5).

A trilha da ADR 040 registrava só login e 403. A exportação em massa, a exclusão de
liderança e a alteração de usuário passam a registrar quem fez, quando e sobre qual registro.
"""
import uuid
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from tests.test_sprint2_endpoints import bearerHeader

LOGS = "/api/v1/plataforma/logs"


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def registrosDo(client: TestClient, evento: str) -> list:
    plataforma = bearerHeader(str(uuid.uuid4()), role="super_admin")
    resposta = client.get(LOGS, headers=plataforma, params={"evento": evento, "limite": 500})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_exportacao_de_dados_fica_registrada(client: TestClient):
    tenant = str(uuid.uuid4())
    assert client.get("/api/v1/gabinete/exportar-dados", headers=bearerHeader(tenant)).status_code == 200

    registros = registrosDo(client, "exportacao_dados")
    assert any(r["email"] == f"tenant-{tenant}@teste.datapolirs.com.br" and str(r["tenant_id"]) == tenant
               for r in registros)


def test_exclusao_de_lideranca_fica_registrada_com_o_id(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)
    criada = client.post("/api/v1/gabinete/liderancas", headers=headers,
                         json={"nm_completo": "Liderança a excluir", "municipios": ["4314902"]})
    idLideranca = criada.json()["id_lideranca"]
    assert client.delete(f"/api/v1/gabinete/liderancas/{idLideranca}", headers=headers).status_code == 204

    registros = registrosDo(client, "lideranca_excluida")
    assert any(idLideranca in (r["caminho"] or "") and str(r["tenant_id"]) == tenant for r in registros)


def test_alteracao_de_usuario_fica_registrada(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)
    novo = client.post("/api/v1/gabinete/usuarios", headers=headers, json={
        "email": f"operador-{tenant[:8]}@teste.datapolirs.com.br", "password": "senha-forte-123", "role": "operador"})
    idUsuario = novo.json()["id"]
    assert client.patch(f"/api/v1/gabinete/usuarios/{idUsuario}", headers=headers,
                        json={"role": "leitor"}).status_code == 200

    registros = registrosDo(client, "usuario_alterado")
    assert any(idUsuario in (r["caminho"] or "") and str(r["tenant_id"]) == tenant for r in registros)
