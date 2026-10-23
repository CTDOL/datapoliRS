"""Super-admin da plataforma (ADR 037): cria, lista, desativa gabinetes e redefine senha de admin."""
import uuid

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from app.services.plataforma_service import PLATAFORMA_TENANT_ID
from tests.test_sprint2_endpoints import bearerHeader

GABINETES = "/api/v1/plataforma/gabinetes"
LOGIN = "/api/v1/auth/login"


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def _email_unico() -> str:
    return f"admin-{uuid.uuid4().hex[:12]}@teste.datapolirs.com.br"


def _criar(client, headers, email, senha="senha-inicial-123"):
    return client.post(GABINETES, headers=headers, json={
        "nm_mandato": "Gabinete Criado Pelo Super-Admin",
        "ds_cargo_mandato": "Deputado Estadual",
        "email_admin": email,
        "senha_inicial": senha,
    })


def _login(client, email, senha):
    """Tenta entrar e descarta o cookie de sessão: ele tem prioridade sobre o token do cabeçalho
    e, se ficasse no cliente compartilhado, faria as chamadas seguintes agirem como esse usuário."""
    resposta = client.post(LOGIN, data={"username": email, "password": senha},
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    client.cookies.clear()
    return resposta


def test_super_admin_nao_ve_o_gabinete_da_plataforma(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    resposta = client.get(GABINETES, headers=headers)

    assert resposta.status_code == 200
    ids = [g["id_tenant"] for g in resposta.json()]
    assert str(PLATAFORMA_TENANT_ID) not in ids


def test_super_admin_cria_gabinete_e_o_admin_consegue_entrar(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    email = _email_unico()

    criado = _criar(client, headers, email)
    assert criado.status_code == 201

    entrada = _login(client, email, "senha-inicial-123")
    assert entrada.status_code == 200


def test_criar_com_email_ja_usado_retorna_conflito(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    email = _email_unico()
    assert _criar(client, headers, email).status_code == 201

    assert _criar(client, headers, email).status_code == 409


def test_admin_comum_nao_acessa_a_plataforma(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")

    assert client.get(GABINETES, headers=headers).status_code == 403
    assert _criar(client, headers, _email_unico()).status_code == 403


def test_desativar_gabinete_bloqueia_o_login_do_admin(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    email = _email_unico()
    criado = _criar(client, headers, email)
    assert criado.status_code == 201
    id_tenant = _id_do_gabinete(client, headers, email)

    desativado = client.patch(f"{GABINETES}/{id_tenant}", headers=headers, json={"is_ativo": False})
    assert desativado.status_code == 204

    assert _login(client, email, "senha-inicial-123").status_code != 200


def test_nao_desativa_o_gabinete_da_plataforma(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")

    resposta = client.patch(f"{GABINETES}/{PLATAFORMA_TENANT_ID}", headers=headers, json={"is_ativo": False})

    assert resposta.status_code == 400


def test_redefine_senha_do_admin_do_gabinete(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    email = _email_unico()
    assert _criar(client, headers, email).status_code == 201
    id_tenant = _id_do_gabinete(client, headers, email)

    trocada = client.post(f"{GABINETES}/{id_tenant}/admin/senha", headers=headers,
                          json={"email_admin": email, "senha_nova": "nova-senha-456"})

    assert trocada.status_code == 204
    assert _login(client, email, "nova-senha-456").status_code == 200
    assert _login(client, email, "senha-inicial-123").status_code != 200


def _id_do_gabinete(client, headers, email):
    for gabinete in client.get(GABINETES, headers=headers).json():
        if gabinete["emails_admin"] and email in gabinete["emails_admin"]:
            return gabinete["id_tenant"]
    raise AssertionError(f"gabinete do admin {email} não encontrado")


def test_admin_de_gabinete_nao_altera_configuracoes_nem_pleito_da_plataforma(client):
    """Configurações globais e manutenção de dados eleitorais valem para todos os gabinetes:
    são do super_admin, não do admin de um gabinete (ADR 037)."""
    headers = bearerHeader(str(uuid.uuid4()), role="admin")

    assert client.get("/api/v1/admin/configuracoes", headers=headers).status_code == 403
    assert client.get("/api/v1/admin/manutencao/saude", headers=headers).status_code == 403


def test_admin_novo_so_acessa_depois_de_trocar_a_senha(client):
    """Usuário com senha pendente (ADR 037): só /me, troca de senha e logout respondem."""
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    email = _email_unico()
    assert _criar(client, headers, email).status_code == 201

    entrada = client.post(LOGIN, data={"username": email, "password": "senha-inicial-123"},
                          headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert entrada.status_code == 200
    try:
        assert client.get("/api/v1/auth/me").json()["must_change_password"] is True
        assert client.get("/api/v1/gabinete/liderancas").status_code == 403

        trocada = client.post("/api/v1/auth/trocar-senha",
                              json={"senha_atual": "senha-inicial-123", "nova_senha": "senha-definitiva-789"})
        assert trocada.status_code == 200

        assert client.get("/api/v1/auth/me").json()["must_change_password"] is False
        assert client.get("/api/v1/gabinete/liderancas").status_code == 200
    finally:
        client.cookies.clear()


def test_super_admin_nao_acessa_dados_de_gabinete(client):
    """A conta da plataforma não lê nem altera dados de gabinete (ADR 039)."""
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")

    assert client.get("/api/v1/gabinete/liderancas", headers=headers).status_code == 403
    assert client.get("/api/v1/gabinete/perfil", headers=headers).status_code == 403
    assert client.get("/api/v1/gabinete/tema", headers=headers).status_code == 403
