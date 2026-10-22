import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_sprint2_endpoints import bearerHeader
from etl.registro_carga import calcularSha256, registrarCarga
from datetime import datetime, timezone


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as testClient:
        yield testClient


def test_saude_e_cargas_requerem_admin(client: TestClient):
    adminHeaders = bearerHeader(str(uuid.uuid4()), role="admin")
    operadorHeaders = bearerHeader(str(uuid.uuid4()), role="operador")

    saude = client.get("/api/v1/admin/manutencao/saude", headers=adminHeaders)
    assert saude.status_code == 200
    assert isinstance(saude.json(), list)

    cargas = client.get("/api/v1/admin/manutencao/cargas?limite=5", headers=adminHeaders)
    assert cargas.status_code == 200
    assert isinstance(cargas.json(), list)

    assert client.get("/api/v1/admin/manutencao/saude", headers=operadorHeaders).status_code == 403
    assert client.get("/api/v1/admin/manutencao/cargas", headers=operadorHeaders).status_code == 403


def test_saude_traz_campos_de_qualidade_por_pleito(client: TestClient):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")
    registros = client.get("/api/v1/admin/manutencao/saude", headers=headers).json()
    for registro in registros:
        for campo in ("cd_eleicao", "ano_eleicao", "linhas_votacao", "municipios_votacao",
                      "zonas_votacao", "linhas_comparecimento"):
            assert campo in registro


def test_sha256_e_deterministico(tmp_path):
    arquivo = tmp_path / "amostra.csv"
    arquivo.write_bytes(b"CD_ELEICAO;ANO\n6259;2026\n")
    assert calcularSha256(str(arquivo)) == calcularSha256(str(arquivo))
    assert len(calcularSha256(str(arquivo))) == 64


def test_registro_de_carga_nao_derruba_a_carga_quando_arquivo_falta(tmp_path):
    """Se o registro falhar (aqui: arquivo inexistente), a carga não pode ser afetada."""
    registrarCarga(
        tipo="votacao", ano=2026, caminhoArquivo=str(tmp_path / "nao_existe.csv"),
        iniciadoEm=datetime.now(timezone.utc), sucesso=True, linhas=1, cdEleicoes=["6259"],
    )
