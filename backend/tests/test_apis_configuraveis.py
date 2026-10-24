"""APIs externas configuráveis pelo super-admin: endereço https, liga/desliga e uso real nas integrações."""
import uuid

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.main import app
from app.core.rate_limit import RateLimiter
from app.services.apis_service import FONTES
from app.services.legislative_sources import buscar_em_todas_fontes, obter_adaptador, CamaraAdapter
from tests.test_sprint2_endpoints import bearerHeader

APIS = "/api/v1/admin/apis"
CONFIG_GERAL = "/api/v1/admin/configuracoes"


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def _todas(ativa: bool, base_overrides=None):
    base_overrides = base_overrides or {}
    return {
        "fontes": [
            {"fonte": f, "base_url": base_overrides.get(f, padrao), "ativa": ativa}
            for f, padrao in FONTES.items()
        ]
    }


def _restaurar(client, headers):
    client.put(APIS, headers=headers, json=_todas(True))


def test_lista_as_fontes_com_os_enderecos_padrao(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    resposta = client.get(APIS, headers=headers)

    assert resposta.status_code == 200
    por_fonte = {f["fonte"]: f for f in resposta.json()["fontes"]}
    assert set(por_fonte) == {"tse", "camara", "senado", "alrs"}
    assert por_fonte["camara"]["base_url"] == FONTES["camara"]
    assert por_fonte["camara"]["ativa"] is True


def test_endereco_sem_https_e_recusado(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    resposta = client.put(APIS, headers=headers, json=_todas(True, {"camara": "http://dadosabertos.exemplo.test/api"}))

    assert resposta.status_code == 422
    assert "https" in resposta.json()["detail"]


def test_endereco_https_e_gravado_e_restaurado(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    try:
        resposta = client.put(APIS, headers=headers, json=_todas(True, {"camara": "https://espelho.exemplo.test/api/v2"}))

        assert resposta.status_code == 200
        por_fonte = {f["fonte"]: f for f in resposta.json()["fontes"]}
        assert por_fonte["camara"]["base_url"] == "https://espelho.exemplo.test/api/v2"
    finally:
        _restaurar(client, headers)


def test_desligar_tse_responde_503_na_consulta(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    try:
        client.put(APIS, headers=headers, json={"fontes": [{"fonte": "tse", "base_url": FONTES["tse"], "ativa": False}]})

        resposta = client.get("/api/v1/candidatas/rs", params={"nome": "Nadine"}, headers=headers)

        assert resposta.status_code == 503
    finally:
        _restaurar(client, headers)


def test_admin_do_gabinete_nao_acessa_as_apis(client):
    headers = bearerHeader(str(uuid.uuid4()), role="admin")

    assert client.get(APIS, headers=headers).status_code == 403
    assert client.put(APIS, headers=headers, json=_todas(True)).status_code == 403


def test_configuracao_geral_nao_altera_chaves_de_api(client):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    resposta = client.put(CONFIG_GERAL, headers=headers, json={"valores": {"api.camara.base_url": "https://x.exemplo.test"}})

    assert resposta.status_code == 400
    assert "tela de APIs" in resposta.json()["detail"]


def test_obter_adaptador_usa_o_endereco_configurado():
    adaptador = obter_adaptador("CAMARA", "https://espelho.exemplo.test/api/v2")

    assert isinstance(adaptador, CamaraAdapter)
    assert adaptador.base_url == "https://espelho.exemplo.test/api/v2"
    assert obter_adaptador("CAMARA").base_url == CamaraAdapter.BASE_URL


@pytest.mark.asyncio
async def test_fonte_desligada_nao_e_consultada():
    # Todas desligadas: nenhuma rede é usada e a busca volta vazia, sem tratar como erro.
    resultados, erros = await buscar_em_todas_fontes("nadine", None, {"ALRS", "CAMARA", "SENADO"})

    assert resultados == []
    assert erros == []
