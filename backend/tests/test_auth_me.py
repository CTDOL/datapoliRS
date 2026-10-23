import uuid

from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from tests.test_sprint2_endpoints import bearerHeader


def test_me_devolve_o_nome_do_gabinete_do_usuario(monkeypatch):
    # O limitador só atrapalha aqui: o teste faz uma chamada.
    async def semLimite(self, request):
        return None
    monkeypatch.setattr(RateLimiter, "__call__", semLimite)

    tenantId = str(uuid.uuid4())
    with TestClient(app) as client:
        resposta = client.get("/api/v1/auth/me", headers=bearerHeader(tenantId))

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["tenant_id"] == tenantId
    assert corpo["role"] == "admin"
    assert corpo["nm_mandato"] == "Tenant de Teste"
