"""Regras de gabinete corrigidas na revisão de 2026-10-24.

- M3: a exportação CSV (aberta no Excel) neutraliza valores que começam como fórmula.
- M4: o gabinete não fica sem administrador ativo.
- M7: o status da tarefa só aceita os valores do domínio.
"""
import csv
import io
import uuid
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from tests.test_sprint2_endpoints import bearerHeader

EXPORTAR = "/api/v1/gabinete/exportar-dados"
USUARIOS = "/api/v1/gabinete/usuarios"
LIDERANCAS = "/api/v1/gabinete/liderancas"
TAREFAS = "/api/v1/gabinete/tarefas"


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


# --- M3: injeção de fórmula no CSV ------------------------------------------------------

def test_exportacao_neutraliza_valores_que_comecam_como_formula(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)
    criada = client.post(LIDERANCAS, headers=headers, json={
        "nm_completo": '=HYPERLINK("http://exemplo.invalido","clique")',
        "nr_telefone": "+55 51 99999-0000",
        "ds_observacoes": "@SUM(1+1)",
        "municipios": ["4314902"],
    })
    assert criada.status_code == 201, criada.text

    resposta = client.get(EXPORTAR, headers=headers)
    assert resposta.status_code == 200
    celulas = [c for linha in csv.reader(io.StringIO(resposta.text.lstrip("﻿"))) for c in linha]
    assert "'=HYPERLINK(\"http://exemplo.invalido\",\"clique\")" in celulas
    assert "'+55 51 99999-0000" in celulas
    assert "'@SUM(1+1)" in celulas
    assert not [c for c in celulas if c[:1] in ("=", "+", "-", "@")]

    client.delete(f"{LIDERANCAS}/{criada.json()['id_lideranca']}", headers=headers)


# --- M4: último administrador ---------------------------------------------------------

def idDoUsuario(client: TestClient, headers: dict, email: str) -> str:
    usuarios = client.get(USUARIOS, headers=headers).json()
    return next(u["id"] for u in usuarios if u["email"] == email)


def test_unico_admin_nao_pode_se_rebaixar(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)
    meuId = idDoUsuario(client, headers, f"tenant-{tenant}@teste.datapolirs.com.br")

    resposta = client.patch(f"{USUARIOS}/{meuId}", headers=headers, json={"role": "leitor"})

    assert resposta.status_code == 400
    assert "administrador" in resposta.json()["detail"]


def test_admin_pode_se_rebaixar_quando_ha_outro_admin_ativo(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)
    meuId = idDoUsuario(client, headers, f"tenant-{tenant}@teste.datapolirs.com.br")
    outro = client.post(USUARIOS, headers=headers, json={
        "email": f"segundo-admin-{tenant[:8]}@teste.datapolirs.com.br",
        "password": "senha-forte-123", "role": "admin"})
    assert outro.status_code == 201, outro.text

    resposta = client.patch(f"{USUARIOS}/{meuId}", headers=headers, json={"role": "operador"})

    assert resposta.status_code == 200
    assert resposta.json()["role"] == "operador"


def test_admin_inativo_nao_conta_como_administrador_restante(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)
    meuId = idDoUsuario(client, headers, f"tenant-{tenant}@teste.datapolirs.com.br")
    outro = client.post(USUARIOS, headers=headers, json={
        "email": f"admin-inativo-{tenant[:8]}@teste.datapolirs.com.br",
        "password": "senha-forte-123", "role": "admin"})
    assert outro.status_code == 201, outro.text
    assert client.patch(f"{USUARIOS}/{outro.json()['id']}", headers=headers,
                        json={"is_active": False}).status_code == 200

    resposta = client.patch(f"{USUARIOS}/{meuId}", headers=headers, json={"role": "leitor"})

    assert resposta.status_code == 400


# --- M7: domínio do status da tarefa ----------------------------------------------------

def test_status_fora_do_dominio_e_recusado(client: TestClient):
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant)

    assert client.post(TAREFAS, headers=headers, json={"titulo": "Status inválido", "tp_status": "x"}).status_code == 422

    tarefa = client.post(TAREFAS, headers=headers, json={"titulo": "Status válido"})
    assert tarefa.status_code == 201
    idTarefa = tarefa.json()["id_tarefa"]
    assert client.put(f"{TAREFAS}/{idTarefa}", headers=headers, json={"tp_status": "x"}).status_code == 422
    assert client.put(f"{TAREFAS}/{idTarefa}", headers=headers, json={"tp_status": "Em Andamento"}).status_code == 200

    client.delete(f"{TAREFAS}/{idTarefa}", headers=headers)


def test_banco_recusa_status_fora_do_dominio_mesmo_sem_passar_pela_api():
    """O CHECK no banco é a garantia para qualquer caminho que não passe pelo schema."""
    import asyncio
    import asyncpg
    from app.core.config import settings

    async def _inserir():
        connection = await asyncpg.connect(dsn=settings.DATABASE_URL)
        tenant = uuid.uuid4()
        try:
            await connection.execute(
                "INSERT INTO tb_tenants (id_tenant, nm_mandato, ds_cargo_mandato) VALUES ($1, 'Teste', 'Teste')", tenant)
            with pytest.raises(asyncpg.exceptions.CheckViolationError):
                await connection.execute(
                    "INSERT INTO tb_gabinete_tarefas (tenant_id, titulo, tp_status) VALUES ($1, 'x', 'Inexistente')", tenant)
        finally:
            await connection.execute("DELETE FROM tb_tenants WHERE id_tenant = $1", tenant)
            await connection.close()
    asyncio.run(_inserir())
