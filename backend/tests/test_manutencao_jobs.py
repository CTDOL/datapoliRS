import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_sprint2_endpoints import bearerHeader
from etl import download_tse, worker
from etl.db_connection import getPostgresConnection


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as testClient:
        yield testClient


def _limpar_jobs_de_teste(idsJob):
    if not idsJob:
        return
    connection = getPostgresConnection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tb_job_etl WHERE id_job = ANY(%s)", (idsJob,))
        connection.commit()
    finally:
        connection.close()


def test_enfileirar_exige_admin(client: TestClient):
    operador = bearerHeader(str(uuid.uuid4()), role="operador")
    resposta = client.post(
        "/api/v1/admin/manutencao/jobs",
        headers=operador,
        json={"tipo": "votacao", "ano": 2026, "confirmacao": "CARREGAR VOTACAO 2026"},
    )
    assert resposta.status_code == 403


def test_confirmacao_errada_nao_enfileira(client: TestClient):
    admin = bearerHeader(str(uuid.uuid4()), role="super_admin")
    resposta = client.post(
        "/api/v1/admin/manutencao/jobs",
        headers=admin,
        json={"tipo": "votacao", "ano": 2026, "confirmacao": "sim"},
    )
    assert resposta.status_code == 400
    assert "CARREGAR VOTACAO 2026" in resposta.json()["detail"]


def test_tipo_e_ano_invalidos_sao_rejeitados(client: TestClient):
    admin = bearerHeader(str(uuid.uuid4()), role="super_admin")
    assert client.post("/api/v1/admin/manutencao/jobs", headers=admin,
                       json={"tipo": "outro", "ano": 2026, "confirmacao": "x"}).status_code == 422
    assert client.post("/api/v1/admin/manutencao/jobs", headers=admin,
                       json={"tipo": "votacao", "ano": 1500, "confirmacao": "x"}).status_code == 422


def test_so_um_job_ativo_por_vez(client: TestClient):
    admin = bearerHeader(str(uuid.uuid4()), role="super_admin")
    corpo = {"tipo": "comparecimento", "ano": 2026, "confirmacao": "CARREGAR COMPARECIMENTO 2026"}
    criado = []
    try:
        primeiro = client.post("/api/v1/admin/manutencao/jobs", headers=admin, json=corpo)
        assert primeiro.status_code == 202
        criado.append(primeiro.json()["id_job"])
        assert primeiro.json()["status"] == "pendente"

        segundo = client.post("/api/v1/admin/manutencao/jobs", headers=admin, json=corpo)
        assert segundo.status_code == 409
    finally:
        _limpar_jobs_de_teste(criado)


def test_download_nao_refaz_zip_existente(tmp_path, monkeypatch):
    monkeypatch.setattr(download_tse, "DATA_DIR", str(tmp_path))
    existente = tmp_path / "votacao_1999.zip"
    existente.write_bytes(b"PK")
    assert download_tse.baixarZipTse("votacao", 1999) == str(existente)


def test_tipo_de_download_desconhecido_falha(tmp_path, monkeypatch):
    monkeypatch.setattr(download_tse, "DATA_DIR", str(tmp_path))
    with pytest.raises(ValueError):
        download_tse.baixarZipTse("outro", 2026)


def test_worker_marca_sucesso(monkeypatch):
    chamadas = {}
    monkeypatch.setattr(worker, "baixarZipTse", lambda tipo, ano: chamadas.setdefault("zip", (tipo, ano)))
    monkeypatch.setitem(worker.CARGAS, "votacao", lambda ano: chamadas.setdefault("carga", ano))
    monkeypatch.setattr(worker, "concluirJob", lambda idJob, sucesso, erro=None: chamadas.setdefault("fim", (idJob, sucesso, erro)))

    assert worker.processarJob({"id_job": 7, "tipo": "votacao", "ano_eleicao": 2026}) is True
    assert chamadas == {"zip": ("votacao", 2026), "carga": 2026, "fim": (7, True, None)}


def test_worker_marca_falha_com_erro(monkeypatch):
    registrado = {}

    def carga_quebrada(ano):
        raise RuntimeError("CSV corrompido")

    monkeypatch.setattr(worker, "baixarZipTse", lambda tipo, ano: None)
    monkeypatch.setitem(worker.CARGAS, "comparecimento", carga_quebrada)
    monkeypatch.setattr(worker, "concluirJob", lambda idJob, sucesso, erro=None: registrado.update(
        idJob=idJob, sucesso=sucesso, erro=erro))

    assert worker.processarJob({"id_job": 9, "tipo": "comparecimento", "ano_eleicao": 2026}) is False
    assert registrado == {"idJob": 9, "sucesso": False, "erro": "CSV corrompido"}


def test_ativar_pleito_inexistente_404(client: TestClient):
    admin = bearerHeader(str(uuid.uuid4()), role="super_admin")
    resposta = client.post("/api/v1/admin/manutencao/ativar-pleito", headers=admin,
                           json={"cd_eleicao": "000000", "confirmacao": "ATIVAR 2026"})
    assert resposta.status_code == 404


def test_ativar_pleito_sem_carga_concluida_409(client: TestClient):
    """TESTE2022 não tem carga registrada: não pode virar o pleito ativo."""
    admin = bearerHeader(str(uuid.uuid4()), role="super_admin")
    resposta = client.post("/api/v1/admin/manutencao/ativar-pleito", headers=admin,
                           json={"cd_eleicao": "TESTE2022", "confirmacao": "ATIVAR 2022"})
    assert resposta.status_code == 409


@pytest.fixture
def pleito_com_carga_ok():
    """Pleito de teste com carga de votação concluída: chega ao gate de confirmação sem depender de dados do TSE."""
    cdEleicao = "TESTE_ATIVAR_2026"
    connection = getPostgresConnection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tb_eleicoes (cd_eleicao, ano_eleicao, nr_turno, tp_abrangencia, ds_eleicao, dt_eleicao)
                VALUES (%s, 2026, 1, 'E', 'Eleição de Teste Ativação', '2026-10-04')
                ON CONFLICT (cd_eleicao) DO NOTHING;
                """,
                (cdEleicao,),
            )
            cursor.execute(
                """
                INSERT INTO tb_carga_etl (tipo, ano_eleicao, cd_eleicoes, arquivo_origem, sha256, tamanho_bytes,
                                          iniciado_em, status, linhas_carregadas)
                VALUES ('votacao', 2026, %s, 'teste-ativacao.csv', %s, 1, NOW(), 'sucesso', 1);
                """,
                ([cdEleicao], "0" * 64),
            )
        connection.commit()
        yield cdEleicao
    finally:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tb_carga_etl WHERE arquivo_origem = 'teste-ativacao.csv';")
            cursor.execute("DELETE FROM tb_eleicoes WHERE cd_eleicao = %s;", (cdEleicao,))
        connection.commit()
        connection.close()


def test_ativar_pleito_com_confirmacao_errada_nao_ativa(client: TestClient, pleito_com_carga_ok: str):
    """Confirmação errada é recusada (400) e nunca grava a troca nem a auditoria."""
    admin = bearerHeader(str(uuid.uuid4()), role="super_admin")
    resposta = client.post("/api/v1/admin/manutencao/ativar-pleito", headers=admin,
                           json={"cd_eleicao": pleito_com_carga_ok, "confirmacao": "sim",
                                 "aceitar_codigos_sem_cadastro": True})
    assert resposta.status_code == 400


def test_ativar_pleito_requer_admin(client: TestClient):
    operador = bearerHeader(str(uuid.uuid4()), role="operador")
    resposta = client.post("/api/v1/admin/manutencao/ativar-pleito", headers=operador,
                           json={"cd_eleicao": "6259", "confirmacao": "ATIVAR 2026"})
    assert resposta.status_code == 403
