import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_sprint2_endpoints import bearerHeader


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as testClient:
        yield testClient


def test_votos_legado_de_numero_inexistente_retorna_404_e_nao_500(client: TestClient):
    """Regressão: a rota legada chamava o método de instância sem self, e respondia 500."""
    admin = bearerHeader(str(uuid.uuid4()), role="admin")
    resposta = client.get("/api/v1/candidatas/99999/votos", headers=admin)
    assert resposta.status_code == 404


def test_eleicao_ativa_exige_login_e_devolve_ano_e_codigo(client: TestClient):
    """O rótulo 'Votação · <ano>' depende deste endpoint: precisa existir, exigir login e devolver os dois campos."""
    assert client.get("/api/v1/eleicao-ativa").status_code == 401
    operador = bearerHeader(str(uuid.uuid4()), role="operador")
    resposta = client.get("/api/v1/eleicao-ativa", headers=operador)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert isinstance(corpo["ano_eleicao"], int)
    assert isinstance(corpo["cd_eleicao"], str)
