"""Limitador de requisições e limite de falhas de login por conta (revisão de 2026-10-24, achado A1).

Antes: a chave do limitador usava o header X-Tenant-ID, escolhido pelo cliente, e não tinha
o escopo da rota. Trocar o header zerava o limite, e rotas com a mesma janela dividiam o
contador. O login não tinha limite por conta, só por IP, e atrás do proxy todos os usuários
chegavam com o IP do container do frontend.
"""
import asyncio
import uuid
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from starlette.requests import Request as StarletteRequest
from app.main import app
from app.core import redis_client
from app.core.rate_limit import RateLimiter, RateLimitExceededException

LOGIN = "/api/v1/auth/login"


def requisicao(ip: str, tenantHeader: str) -> StarletteRequest:
    return StarletteRequest({
        "type": "http", "method": "POST", "path": "/teste", "query_string": b"",
        "headers": [(b"x-tenant-id", tenantHeader.encode())],
        "client": (ip, 40000),
    })


def chamar(limitador: RateLimiter, ip: str, tenantHeader: str = "public") -> None:
    async def _chamar():
        await redis_client.initializeRedisClient()
        assert redis_client.redisClientInstance is not None, "Redis indisponível: o limitador liberaria tudo"
        await limitador(requisicao(ip, tenantHeader))
    asyncio.run(_chamar())


def escopoNovo() -> str:
    # Escopo exclusivo por teste: o Redis é compartilhado entre execuções.
    return f"teste-{uuid.uuid4().hex[:12]}"


def test_trocar_o_header_x_tenant_id_nao_zera_o_limite():
    limitador = RateLimiter(times=2, seconds=60, configKey=escopoNovo())
    chamar(limitador, "203.0.113.10", "a")
    chamar(limitador, "203.0.113.10", "b")
    with pytest.raises(RateLimitExceededException):
        chamar(limitador, "203.0.113.10", "c")


def test_rotas_diferentes_nao_dividem_o_contador():
    rotaA = RateLimiter(times=2, seconds=60, configKey=escopoNovo())
    rotaB = RateLimiter(times=2, seconds=60, configKey=escopoNovo())
    chamar(rotaA, "203.0.113.20")
    chamar(rotaA, "203.0.113.20")
    chamar(rotaB, "203.0.113.20")  # contador próprio: não pode estourar


def test_ips_diferentes_tem_contadores_proprios():
    limitador = RateLimiter(times=1, seconds=60, configKey=escopoNovo())
    chamar(limitador, "203.0.113.30")
    chamar(limitador, "203.0.113.31")


@pytest.fixture(scope="module")
def client():
    # Só o limite por IP fica desligado: o objeto aqui é o limite por conta.
    async def semLimite(self, request: Request):
        return None
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


def tentarLogin(client: TestClient, email: str, senha: str = "senha-errada-123") -> int:
    resposta = client.post(LOGIN, data={"username": email, "password": senha},
                           headers={"Content-Type": "application/x-www-form-urlencoded"})
    client.cookies.clear()
    return resposta.status_code


def test_falhas_seguidas_na_mesma_conta_bloqueiam_o_login(client: TestClient):
    email = f"alvo-{uuid.uuid4().hex[:10]}@teste.datapolirs.com.br"
    codigos = [tentarLogin(client, email) for _ in range(10)]
    assert codigos == [401] * 10
    assert tentarLogin(client, email) == 429


def test_bloqueio_de_uma_conta_nao_atinge_outra(client: TestClient):
    email = f"alvo-{uuid.uuid4().hex[:10]}@teste.datapolirs.com.br"
    for _ in range(11):
        tentarLogin(client, email)
    outra = f"outra-{uuid.uuid4().hex[:10]}@teste.datapolirs.com.br"
    assert tentarLogin(client, outra) == 401


def test_conta_e_comparada_sem_diferenciar_maiusculas(client: TestClient):
    email = f"alvo-{uuid.uuid4().hex[:10]}@teste.datapolirs.com.br"
    for _ in range(10):
        tentarLogin(client, email)
    assert tentarLogin(client, email.upper()) == 429
