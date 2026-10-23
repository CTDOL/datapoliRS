"""Observabilidade (ADR 040): trilha de acesso, saúde, alertas simples e expurgo de 6 meses."""
import asyncio
import uuid

import asyncpg
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.rate_limit import RateLimiter
from tests.test_sprint2_endpoints import bearerHeader

LOGS = "/api/v1/plataforma/logs"
LOGIN = "/api/v1/auth/login"


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def _login(client, email, senha):
    resposta = client.post(LOGIN, data={"username": email, "password": senha},
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    client.cookies.clear()
    return resposta


def test_login_com_senha_errada_e_registrado(client):
    email = f"falha-{uuid.uuid4().hex[:10]}@teste.datapolirs.com.br"
    assert _login(client, email, "senha-errada-123").status_code == 401

    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    registros = client.get(LOGS, headers=headers, params={"evento": "login_falha"}).json()
    assert any(r["email"] == email for r in registros)


def test_login_bem_sucedido_e_registrado(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    criado_email = f"ok-{uuid.uuid4().hex[:10]}@teste.datapolirs.com.br"
    client.post("/api/v1/plataforma/gabinetes", headers=headers, json={
        "nm_mandato": "Gabinete de Log", "ds_cargo_mandato": "Vereador",
        "email_admin": criado_email, "senha_inicial": "senha-inicial-123"})
    assert _login(client, criado_email, "senha-inicial-123").status_code == 200

    registros = client.get(LOGS, headers=headers, params={"evento": "login_ok"}).json()
    assert any(r["email"] == criado_email for r in registros)


def test_acesso_negado_403_e_registrado_com_o_caminho(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    assert client.get("/api/v1/plataforma/gabinetes", headers=headers).status_code == 403

    admin = bearerHeader(str(uuid.uuid4()), role="super_admin")
    registros = client.get(LOGS, headers=admin, params={"evento": "acesso_negado_403"}).json()
    assert any(r["caminho"] == "/api/v1/plataforma/gabinetes" for r in registros)


def test_admin_de_gabinete_nao_le_a_trilha(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    assert client.get(LOGS, headers=headers).status_code == 403
    assert client.get("/api/v1/plataforma/saude", headers=headers).status_code == 403


def test_saude_informa_banco_e_cache(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    corpo = client.get("/api/v1/plataforma/saude", headers=headers).json()

    assert corpo["banco"]["status"] == "ok"
    assert corpo["api"]["status"] == "ok"
    assert "cache" in corpo


def test_alerta_para_tentativas_repetidas_de_login(client):
    email = f"forca-bruta-{uuid.uuid4().hex[:10]}@teste.datapolirs.com.br"
    for _ in range(5):
        _login(client, email, "errada-1234")

    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    alertas = client.get("/api/v1/plataforma/alertas", headers=headers).json()
    assert any(a["titulo"] == "Tentativas de login repetidas" and email in a["detalhe"] for a in alertas)


def test_expurgo_remove_registros_com_mais_de_6_meses(client):
    async def inserir_antigo():
        conexao = await asyncpg.connect(dsn=settings.DATABASE_URL)
        try:
            await conexao.execute(
                "INSERT INTO tb_log_acesso (created_at, evento, email, caminho) "
                "VALUES (now() - interval '200 days', 'login_falha', 'antigo@teste.com', '/teste-expurgo')")
        finally:
            await conexao.close()

    asyncio.run(inserir_antigo())
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    removidos = client.post(f"{LOGS}/expurgo", headers=headers).json()["removidos"]

    assert removidos >= 1
    restantes = client.get(LOGS, headers=headers, params={"limite": 500}).json()
    assert not any(r["caminho"] == "/teste-expurgo" for r in restantes)


def test_ip_com_varias_contas_tentadas_aparece_como_suspeito(client):
    """O TestClient usa o IP 'testclient'. Cinco contas diferentes erradas a partir dele são suspeitas."""
    for _ in range(3):
        _login(client, f"suspeito-{uuid.uuid4().hex[:10]}@teste.datapolirs.com.br", "errada-1234")

    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    suspeitos = client.get("/api/v1/plataforma/ips-suspeitos", headers=headers).json()

    alvo = next(s for s in suspeitos if s["ip"] == "testclient")
    assert alvo["emails_distintos"] >= 3
    assert any("contas tentadas" in m for m in alvo["motivos"])
    assert alvo["localizacao"] is None


def test_ips_suspeitos_e_restrito_ao_super_admin(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    assert client.get("/api/v1/plataforma/ips-suspeitos", headers=headers).status_code == 403


BASE_TESTE_GEOIP = "/usr/local/Cellar/libmaxminddb/1.14.0/share/examples/GeoIP2-City-Test.mmdb"


def test_localizacao_sem_base_configurada_e_vazia(monkeypatch):
    from app.services import observabilidade_service as obs
    monkeypatch.setattr(settings, "GEOIP_DB_PATH", "")
    monkeypatch.setattr(obs, "_leitor_geoip", None)

    assert obs.localizar("81.2.69.142") is None


def test_ip_privado_nao_tem_localizacao(monkeypatch):
    import os
    from app.services import observabilidade_service as obs
    if not os.path.exists(BASE_TESTE_GEOIP):
        pytest.skip("base de teste da MaxMind não instalada nesta máquina")
    monkeypatch.setattr(settings, "GEOIP_DB_PATH", BASE_TESTE_GEOIP)
    monkeypatch.setattr(obs, "_leitor_geoip", None)

    assert obs.localizar("172.22.0.1") is None
    assert obs.localizar("testclient") is None


def test_ip_publico_e_localizado_pela_base(monkeypatch):
    import os
    from app.services import observabilidade_service as obs
    if not os.path.exists(BASE_TESTE_GEOIP):
        pytest.skip("base de teste da MaxMind não instalada nesta máquina")
    monkeypatch.setattr(settings, "GEOIP_DB_PATH", BASE_TESTE_GEOIP)
    monkeypatch.setattr(obs, "_leitor_geoip", None)

    assert obs.localizar("81.2.69.142") == "London, United Kingdom"
    latitude, longitude = obs.coordenadas("81.2.69.142")
    assert 51 < latitude < 52 and -1 < longitude < 0
    assert obs.coordenadas("172.22.0.1") is None
