import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_sprint2_endpoints import bearerHeader


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as testClient:
        yield testClient


def test_perfil_get_e_put_admin(client: TestClient):
    """Admin consegue ler e atualizar o perfil do próprio gabinete; cd_cargo
    ressincroniza o texto livre legado ds_cargo_mandato."""
    tenantId = str(uuid.uuid4())
    headers = bearerHeader(tenantId, role="admin")

    getResponse = client.get("/api/v1/gabinete/perfil", headers=headers)
    assert getResponse.status_code == 200
    assert getResponse.json()["id_tenant"] == tenantId

    putResponse = client.put(
        "/api/v1/gabinete/perfil",
        headers=headers,
        json={"nm_mandato": "Gabinete Deputado Teste", "cd_cargo": 6},
    )
    assert putResponse.status_code == 200
    data = putResponse.json()
    assert data["nm_mandato"] == "Gabinete Deputado Teste"
    assert data["cd_cargo"] == 6
    assert data["ds_cargo"] == "Deputado Federal"
    assert data["ds_cargo_mandato"] == "Deputado Federal"


def test_perfil_put_requer_papel_admin(client: TestClient):
    """Operador não pode alterar o perfil do mandato (apenas ler)."""
    tenantId = str(uuid.uuid4())
    headers = bearerHeader(tenantId, role="operador")

    getResponse = client.get("/api/v1/gabinete/perfil", headers=headers)
    assert getResponse.status_code == 200

    putResponse = client.put(
        "/api/v1/gabinete/perfil", headers=headers, json={"nm_mandato": "Tentativa Bloqueada"}
    )
    assert putResponse.status_code == 403


def test_usuarios_listagem_isolada_por_tenant(client: TestClient):
    """A listagem de usuários de um gabinete não vaza usuários de outro tenant."""
    tenantA = str(uuid.uuid4())
    tenantB = str(uuid.uuid4())
    headersA = bearerHeader(tenantA, role="admin")
    bearerHeader(tenantB, role="admin")  # garante um usuário existente no tenant B

    response = client.get("/api/v1/gabinete/usuarios", headers=headersA)
    assert response.status_code == 200
    tenantIds = {u["email"] for u in response.json()}
    assert all(tenantB not in email for email in tenantIds)
    assert len(response.json()) >= 1


def test_usuarios_gestao_requer_papel_admin(client: TestClient):
    """Operador não pode listar nem convidar membros do gabinete."""
    tenantId = str(uuid.uuid4())
    headers = bearerHeader(tenantId, role="operador")

    listResponse = client.get("/api/v1/gabinete/usuarios", headers=headers)
    assert listResponse.status_code == 403

    createResponse = client.post(
        "/api/v1/gabinete/usuarios",
        headers=headers,
        json={"email": f"novo-{uuid.uuid4()}@teste.com", "password": "senha1234", "role": "leitor"},
    )
    assert createResponse.status_code == 403


def test_convidar_usuario_email_duplicado_retorna_409(client: TestClient):
    tenantId = str(uuid.uuid4())
    headers = bearerHeader(tenantId, role="admin")
    email = f"duplicado-{uuid.uuid4()}@teste.com"

    first = client.post(
        "/api/v1/gabinete/usuarios",
        headers=headers,
        json={"email": email, "password": "senha1234", "role": "leitor"},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/gabinete/usuarios",
        headers=headers,
        json={"email": email, "password": "outrasenha", "role": "operador"},
    )
    assert second.status_code == 409


def test_nao_pode_desativar_a_propria_conta(client: TestClient):
    """Trava de segurança: um admin autenticado não pode desativar a si mesmo."""
    tenantId = str(uuid.uuid4())
    headers = bearerHeader(tenantId, role="admin")

    me = client.get("/api/v1/auth/me", headers=headers).json()
    users = client.get("/api/v1/gabinete/usuarios", headers=headers).json()
    selfUser = next(u for u in users if u["email"] == me["email"])

    response = client.patch(
        f"/api/v1/gabinete/usuarios/{selfUser['id']}", headers=headers, json={"is_active": False}
    )
    assert response.status_code == 400


def test_trocar_senha_fluxo_completo(client: TestClient):
    """Senha atual incorreta é rejeitada; senha atual correta troca a credencial."""
    tenantId = str(uuid.uuid4())
    headers = bearerHeader(tenantId, role="admin")

    wrongResponse = client.post(
        "/api/v1/auth/trocar-senha",
        headers=headers,
        json={"senha_atual": "senha-errada", "nova_senha": "novaSenhaForte123"},
    )
    assert wrongResponse.status_code == 400

    okResponse = client.post(
        "/api/v1/auth/trocar-senha",
        headers=headers,
        json={"senha_atual": "teste123", "nova_senha": "novaSenhaForte123"},
    )
    assert okResponse.status_code == 200


def test_exportar_dados_requer_papel_admin(client: TestClient):
    tenantId = str(uuid.uuid4())
    adminHeaders = bearerHeader(tenantId, role="admin")
    operadorHeaders = bearerHeader(str(uuid.uuid4()), role="operador")

    adminResponse = client.get("/api/v1/gabinete/exportar-dados", headers=adminHeaders)
    assert adminResponse.status_code == 200
    assert "LIDERANCAS" in adminResponse.text
    assert "EMENDAS ORCAMENTARIAS" in adminResponse.text

    operadorResponse = client.get("/api/v1/gabinete/exportar-dados", headers=operadorHeaders)
    assert operadorResponse.status_code == 403
