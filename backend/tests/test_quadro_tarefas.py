"""Quadro de tarefas e painel de produtividade: quem lê, quem comenta, quem vê o painel e isolamento por gabinete."""
import uuid

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.main import app
from app.core.rate_limit import RateLimiter
from tests.test_sprint2_endpoints import bearerHeader

TAREFAS = "/api/v1/gabinete/tarefas"
PRODUTIVIDADE = "/api/v1/gabinete/produtividade"


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def _nova_tarefa(client, tenant_headers):
    resposta = client.post(TAREFAS, headers=tenant_headers, json={"titulo": "Tarefa de teste do quadro"})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id_tarefa"]


def test_leitor_le_comentarios_mas_nao_comenta(client):
    tenant = str(uuid.uuid4())
    operador = bearerHeader(tenant, role="operador")
    tarefa = _nova_tarefa(client, operador)
    try:
        leitor = bearerHeader(tenant, role="leitor")

        assert client.get(f"{TAREFAS}/{tarefa}/comentarios", headers=leitor).status_code == 200
        assert client.post(f"{TAREFAS}/{tarefa}/comentarios", headers=leitor, json={"texto": "Oi"}).status_code == 403
    finally:
        client.delete(f"{TAREFAS}/{tarefa}", headers=bearerHeader(tenant, role="admin"))


def test_operador_comenta_e_o_comentario_aparece_na_lista(client):
    tenant = str(uuid.uuid4())
    operador = bearerHeader(tenant, role="operador")
    tarefa = _nova_tarefa(client, operador)
    try:
        criado = client.post(f"{TAREFAS}/{tarefa}/comentarios", headers=operador, json={"texto": "  Ligamos para a secretaria  "})

        assert criado.status_code == 201
        assert criado.json()["texto"] == "Ligamos para a secretaria"
        lista = client.get(f"{TAREFAS}/{tarefa}/comentarios", headers=operador).json()
        assert [c["texto"] for c in lista] == ["Ligamos para a secretaria"]
    finally:
        client.delete(f"{TAREFAS}/{tarefa}", headers=bearerHeader(tenant, role="admin"))


def test_comentario_em_tarefa_de_outro_gabinete_e_404(client):
    dono = str(uuid.uuid4())
    outro = str(uuid.uuid4())
    tarefa = _nova_tarefa(client, bearerHeader(dono, role="operador"))
    try:
        resposta = client.post(f"{TAREFAS}/{tarefa}/comentarios", headers=bearerHeader(outro, role="operador"), json={"texto": "Intruso"})

        assert resposta.status_code == 404
    finally:
        client.delete(f"{TAREFAS}/{tarefa}", headers=bearerHeader(dono, role="admin"))


def test_comentario_vazio_e_recusado(client):
    tenant = str(uuid.uuid4())
    operador = bearerHeader(tenant, role="operador")
    tarefa = _nova_tarefa(client, operador)
    try:
        assert client.post(f"{TAREFAS}/{tarefa}/comentarios", headers=operador, json={"texto": "   "}).status_code == 422
    finally:
        client.delete(f"{TAREFAS}/{tarefa}", headers=bearerHeader(tenant, role="admin"))


def test_painel_de_produtividade_e_so_do_admin(client):
    tenant = str(uuid.uuid4())
    tarefa = _nova_tarefa(client, bearerHeader(tenant, role="operador"))
    try:
        # Cada bearerHeader ajusta o papel do mesmo usuário do gabinete: o cabeçalho de admin é gerado por último.
        assert client.get(PRODUTIVIDADE, headers=bearerHeader(tenant, role="operador")).status_code == 403
        assert client.get(PRODUTIVIDADE, headers=bearerHeader(tenant, role="leitor")).status_code == 403

        admin = bearerHeader(tenant, role="admin")
        painel = client.get(PRODUTIVIDADE, headers=admin)

        assert painel.status_code == 200
        totais = painel.json()["tarefas"]
        assert totais["total"] == 1
        assert totais["pendente"] == 1
        assert totais["concluida"] == 0
    finally:
        client.delete(f"{TAREFAS}/{tarefa}", headers=bearerHeader(tenant, role="admin"))
