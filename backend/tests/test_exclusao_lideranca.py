"""Exclusão de liderança: isolamento do disco entre gabinetes e tarefas que a têm como responsável.

Revisão arquitetural de 2026-10-24, achados A2 e A3:
- A2: a rota apagava as fotos do disco antes de conferir o gabinete, e o diretório é único
  para todos os gabinetes. O gabinete B conseguia apagar a foto de uma liderança do A.
- A3: a coluna legada tb_gabinete_tarefas.id_lideranca_responsavel não tinha ON DELETE.
  Excluir a liderança responsável por uma tarefa terminava em 500, e a foto já tinha sido apagada.
"""
import os
import uuid
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from app.routers.cabinet import UPLOADS_DIR
from tests.test_foto_sanitizacao import jpegComGps, criarLideranca, enviarFoto
from tests.test_sprint2_endpoints import bearerHeader

LIDERANCAS = "/api/v1/gabinete/liderancas"
TAREFAS = "/api/v1/gabinete/tarefas"


@pytest.fixture(scope="module")
def client():
    # O limitador não é o objeto destes testes (ver test_isolamento_tenant.py).
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def caminhoDaFoto(resposta) -> str:
    return os.path.join(UPLOADS_DIR, os.path.basename(resposta.json()["ds_foto_url"]))


def test_b_nao_apaga_a_foto_de_lideranca_do_a(client: TestClient):
    tenantA, tenantB = str(uuid.uuid4()), str(uuid.uuid4())
    idLideranca = criarLideranca(client, tenantA)
    foto = enviarFoto(client, tenantA, idLideranca, jpegComGps())
    assert foto.status_code == 200
    caminho = caminhoDaFoto(foto)

    resposta = client.delete(f"{LIDERANCAS}/{idLideranca}", headers=bearerHeader(tenantB))

    assert resposta.status_code == 404
    assert os.path.exists(caminho), "a foto do gabinete A foi apagada por uma requisição do gabinete B"
    client.delete(f"{LIDERANCAS}/{idLideranca}", headers=bearerHeader(tenantA))


def test_excluir_responsavel_principal_passa_a_tarefa_para_o_proximo(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)
    primeira = criarLideranca(client, tenant)
    segunda = criarLideranca(client, tenant)
    tarefa = client.post(TAREFAS, headers=headers, json={
        "titulo": "Tarefa com dois responsáveis", "ids_responsaveis": [primeira, segunda]})
    assert tarefa.status_code == 201, tarefa.text
    idTarefa = tarefa.json()["id_tarefa"]
    assert tarefa.json()["id_lideranca_responsavel"] == primeira

    assert client.delete(f"{LIDERANCAS}/{primeira}", headers=headers).status_code == 204

    restante = client.get(TAREFAS, headers=headers).json()
    registro = next(t for t in restante if t["id_tarefa"] == idTarefa)
    assert [r["id_lideranca"] for r in registro["responsaveis"]] == [segunda]
    assert registro["id_lideranca_responsavel"] == segunda

    client.delete(f"{TAREFAS}/{idTarefa}", headers=headers)
    client.delete(f"{LIDERANCAS}/{segunda}", headers=headers)


def test_excluir_unico_responsavel_mantem_a_tarefa_e_a_foto_sai_do_disco(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)
    idLideranca = criarLideranca(client, tenant)
    foto = enviarFoto(client, tenant, idLideranca, jpegComGps())
    caminho = caminhoDaFoto(foto)
    tarefa = client.post(TAREFAS, headers=headers, json={
        "titulo": "Tarefa com um responsável", "ids_responsaveis": [idLideranca]})
    assert tarefa.status_code == 201, tarefa.text
    idTarefa = tarefa.json()["id_tarefa"]

    assert client.delete(f"{LIDERANCAS}/{idLideranca}", headers=headers).status_code == 204

    registro = client.get(f"{TAREFAS}", headers=headers).json()
    registro = next(t for t in registro if t["id_tarefa"] == idTarefa)
    assert registro["responsaveis"] == []
    assert registro["id_lideranca_responsavel"] is None
    assert not os.path.exists(caminho)

    client.delete(f"{TAREFAS}/{idTarefa}", headers=headers)
