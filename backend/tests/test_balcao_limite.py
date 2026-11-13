"""[BAL-02] Limite de requisições do portal público (Issue #39).

O portal aceita 5 envios por 60 s por IP (configKey "balcao_portal"). O 6º devolve 429. Se o Redis cair, o
portal FALHA FECHADO: 503 em vez de ficar sem limite. É uma opção nova do RateLimiter; as demais rotas
continuam liberando o tráfego (fail-open), como antes.

Cada teste usa um IP próprio para o contador do Redis não vazar de um teste para o outro.
"""
import random
import uuid

import pytest
from fastapi.testclient import TestClient
from app.core import redis_client
from app.main import app
from tests.balcao_apoio import (
    CAIXA, PORTAL, consultar, criarPortalNoBanco, criarTenant, rotaRegistrada, url,
)
from tests.test_sprint2_endpoints import bearerHeader


def ipNovo() -> str:
    return f"10.{random.randint(1, 250)}.{random.randint(1, 250)}.{random.randint(1, 250)}"


@pytest.fixture()
def gabinete():
    tenantId = str(uuid.uuid4())
    criarTenant(tenantId)
    portalId, token = criarPortalNoBanco(tenantId)
    return {"tenant": tenantId, "token": token}


@pytest.fixture(autouse=True)
def rotaDoPortalExiste():
    assert rotaRegistrada("POST", PORTAL), f"POST {PORTAL} não está registrada"


def enviar(client, gabinete, texto=None):
    return client.post(url(PORTAL, token=gabinete["token"]), data={"texto": texto or f"Pedido {uuid.uuid4()}"})


def test_sexto_envio_no_minuto_devolve_429_e_os_cinco_primeiros_passam(gabinete):
    with TestClient(app, client=(ipNovo(), 50000)) as client:
        assert [enviar(client, gabinete).status_code for _ in range(5)] == [201] * 5
        sexto = enviar(client, gabinete, texto=f"Sexto {uuid.uuid4()}")
    assert sexto.status_code == 429
    assert sexto.headers["content-type"].startswith("application/problem+json")
    assert gabinete["tenant"] not in sexto.text
    assert len(consultar("SELECT 1 FROM tb_balcao_entradas WHERE tenant_id = $1", gabinete["tenant"])) == 5


def test_o_limite_e_por_ip(gabinete):
    with TestClient(app, client=(ipNovo(), 50000)) as primeiro:
        for _ in range(5):
            enviar(primeiro, gabinete)
        assert enviar(primeiro, gabinete).status_code == 429
    with TestClient(app, client=(ipNovo(), 50000)) as outro:
        assert enviar(outro, gabinete).status_code == 201


def test_redis_fora_devolve_503_no_portal_e_nao_grava(gabinete, monkeypatch):
    monkeypatch.setattr(redis_client, "redisClientInstance", None)
    texto = f"Com Redis fora {uuid.uuid4()}"
    with TestClient(app, client=(ipNovo(), 50000)) as client:
        monkeypatch.setattr(redis_client, "redisClientInstance", None)  # o lifespan reconecta ao subir
        resposta = enviar(client, gabinete, texto=texto)
    assert resposta.status_code == 503
    assert resposta.headers["content-type"].startswith("application/problem+json")
    assert consultar("SELECT 1 FROM tb_balcao_entradas WHERE texto_original = $1", texto) == []


def test_redis_que_falha_no_incr_tambem_devolve_503(gabinete, monkeypatch):
    class RedisQuebrado:
        async def incr(self, *_):
            raise ConnectionError("redis fora")

        async def expire(self, *_):
            raise ConnectionError("redis fora")

        async def get(self, *_):
            return None

        async def aclose(self):
            return None

    with TestClient(app, client=(ipNovo(), 50000)) as client:
        monkeypatch.setattr(redis_client, "redisClientInstance", RedisQuebrado())
        resposta = enviar(client, gabinete)
    assert resposta.status_code == 503


def test_as_demais_rotas_continuam_liberando_o_trafego_sem_redis(monkeypatch):
    """Só o portal falha fechado. A caixa de entrada segue fail-open, como antes."""
    headers = bearerHeader(str(uuid.uuid4()))
    with TestClient(app, client=(ipNovo(), 50000)) as client:
        monkeypatch.setattr(redis_client, "redisClientInstance", None)
        assert client.get(CAIXA, headers=headers).status_code == 200
