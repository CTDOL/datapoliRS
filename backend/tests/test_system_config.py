import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_sprint2_endpoints import bearerHeader


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as testClient:
        yield testClient


def test_listar_configuracoes_requer_admin(client: TestClient):
    adminHeaders = bearerHeader(str(uuid.uuid4()), role="admin")
    operadorHeaders = bearerHeader(str(uuid.uuid4()), role="operador")

    adminResponse = client.get("/api/v1/admin/configuracoes", headers=adminHeaders)
    assert adminResponse.status_code == 200
    data = adminResponse.json()
    assert isinstance(data, list)
    assert any(item["chave"] == "eleitoral.election_year" for item in data)

    operadorResponse = client.get("/api/v1/admin/configuracoes", headers=operadorHeaders)
    assert operadorResponse.status_code == 403


def test_atualizar_configuracao_aplica_e_reverte(client: TestClient):
    """A escrita precisa persistir e refletir na leitura seguinte — sem
    reiniciar o processo (o cache é invalidado a cada PUT).

    Restaura o valor ORIGINAL (lido antes), em finally: o banco de dev é compartilhado,
    e um valor fixo aqui desfazia o pleito ativo a cada rodada de testes."""
    headers = bearerHeader(str(uuid.uuid4()), role="admin")

    original = next(item for item in client.get("/api/v1/admin/configuracoes", headers=headers).json()
                    if item["chave"] == "eleitoral.election_year")["valor"]
    try:
        updateResponse = client.put(
            "/api/v1/admin/configuracoes",
            headers=headers,
            json={"valores": {"eleitoral.election_year": "2026"}},
        )
        assert updateResponse.status_code == 200
        updated = next(item for item in updateResponse.json() if item["chave"] == "eleitoral.election_year")
        assert updated["valor"] == "2026"

        listResponse = client.get("/api/v1/admin/configuracoes", headers=headers)
        persisted = next(item for item in listResponse.json() if item["chave"] == "eleitoral.election_year")
        assert persisted["valor"] == "2026"
    finally:
        client.put(
            "/api/v1/admin/configuracoes",
            headers=headers,
            json={"valores": {"eleitoral.election_year": original}},
        )


def test_atualizar_configuracao_valor_invalido_rejeitado(client: TestClient):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")

    response = client.put(
        "/api/v1/admin/configuracoes",
        headers=headers,
        json={"valores": {"eleitoral.election_year": "nao-e-numero"}},
    )
    assert response.status_code == 400


def test_atualizar_configuracao_chave_desconhecida_rejeitada(client: TestClient):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")

    response = client.put(
        "/api/v1/admin/configuracoes",
        headers=headers,
        json={"valores": {"chave.que.nao.existe": "1"}},
    )
    assert response.status_code == 400
