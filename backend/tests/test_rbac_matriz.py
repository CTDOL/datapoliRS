"""Matriz de permissões por papel (RBAC), aprovada pelo operador em 2026-10-23.

- leitor: só consulta. Nenhuma escrita e nenhuma exportação.
- operador: cria e edita lideranças, emendas, projetos, tarefas e observadores; exporta.
- admin: tudo, inclusive excluir registros e gerenciar a equipe.

Cada permissão negada é um teste negativo. Só valem depois da prova de mutação (Regra 12.4).
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from tests.test_sprint2_endpoints import bearerHeader

LIDERANCAS = "/api/v1/gabinete/liderancas"
EXPORTAR = "/api/v1/gabinete/exportar-dados"
PORTO_ALEGRE = "4314902"


@pytest.fixture(scope="module")
def client():
    # O limitador de requisições não é o objeto destes testes.
    async def semLimite(self, request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def _payload_lideranca(nome: str) -> dict:
    return {"nm_completo": nome, "municipios": [PORTO_ALEGRE]}


def test_leitor_consulta_mas_nao_cria(client):
    tenantId = str(uuid.uuid4())
    headers = bearerHeader(tenantId, role="leitor")

    assert client.get(LIDERANCAS, headers=headers).status_code == 200
    resposta = client.post(LIDERANCAS, headers=headers, json=_payload_lideranca("Tentativa do leitor"))
    assert resposta.status_code == 403


def test_leitor_nao_exporta_dados(client):
    tenantId = str(uuid.uuid4())
    resposta = client.get(EXPORTAR, headers=bearerHeader(tenantId, role="leitor"))
    assert resposta.status_code == 403


def test_operador_cria_lideranca(client):
    tenantId = str(uuid.uuid4())
    resposta = client.post(LIDERANCAS, headers=bearerHeader(tenantId, role="operador"),
                           json=_payload_lideranca("Cadastro do operador"))
    assert resposta.status_code == 201


def test_operador_nao_exclui_lideranca(client):
    tenantId = str(uuid.uuid4())
    headers = bearerHeader(tenantId, role="operador")
    criada = client.post(LIDERANCAS, headers=headers, json=_payload_lideranca("Para excluir"))
    assert criada.status_code == 201

    resposta = client.delete(f"{LIDERANCAS}/{criada.json()['id_lideranca']}", headers=headers)
    assert resposta.status_code == 403


def test_admin_exclui_lideranca(client):
    tenantId = str(uuid.uuid4())
    headers = bearerHeader(tenantId, role="admin")
    criada = client.post(LIDERANCAS, headers=headers, json=_payload_lideranca("Para excluir pelo admin"))
    assert criada.status_code == 201

    resposta = client.delete(f"{LIDERANCAS}/{criada.json()['id_lideranca']}", headers=headers)
    assert resposta.status_code == 204
