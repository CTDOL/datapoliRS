import asyncio
import uuid
import pytest
import asyncpg
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.auth_service import AuthService


@pytest.fixture(scope="module")
def client():
    """Fixture que inicializa o TestClient com o ciclo de vida (lifespan) da aplicação."""
    with TestClient(app) as testClient:
        yield testClient


def createTestUser(email: str, tenantId: str) -> None:
    """Insere (ou reaproveita) um usuário de teste em tb_users para um tenant específico."""
    async def _create():
        connection = await asyncpg.connect(dsn=settings.DATABASE_URL)
        try:
            await connection.execute(
                """
                INSERT INTO tb_users (tenant_id, email, hashed_password, is_active)
                VALUES ($1, $2, $3, TRUE)
                ON CONFLICT (email) DO NOTHING
                """,
                tenantId, email, AuthService.get_password_hash("teste123"),
            )
        finally:
            await connection.close()
    asyncio.run(_create())


def bearerHeader(tenantId: str) -> dict:
    """Gera um Authorization header com um JWT válido para um usuário exclusivo do tenant informado.

    O e-mail é derivado do tenantId para garantir um usuário novo a cada execução —
    tenantId é um UUID aleatório gerado por teste, então reaproveitar um e-mail fixo
    faria o ON CONFLICT manter o tenant_id de uma execução anterior.
    """
    email = f"tenant-{tenantId}@teste.datapolirs.com.br"
    createTestUser(email, tenantId)
    token = AuthService.create_access_token(
        data={"sub": email, "tenant_id": tenantId}
    )
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint(client: TestClient):
    """Testa o endpoint de monitoramento /health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_geo_municipios_endpoint(client: TestClient):
    """Testa se o endpoint /api/v1/geo/municipios retorna um FeatureCollection válido."""
    response = client.get("/api/v1/geo/municipios")
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) > 0


def test_candidatos_search_endpoint(client: TestClient):
    """Testa a pesquisa de candidatos multi-cargo."""
    # Busca sem filtros
    response = client.get("/api/v1/candidatos?limite=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5

    # Busca por cargo Deputado Federal (6)
    responseFederal = client.get("/api/v1/candidatos?cd_cargo=6&limite=5")
    assert responseFederal.status_code == 200
    federalData = responseFederal.json()
    for cand in federalData:
        assert cand["cd_cargo"] == 6


def test_votacao_candidato_por_numero(client: TestClient):
    """Testa a consulta de votação por número eleitoral."""
    response = client.get("/api/v1/votacao/numero/13123")
    assert response.status_code == 200
    data = response.json()
    assert data["nr_candidato"] == 13123
    assert "distribuicao_municipios" in data
    assert len(data["distribuicao_municipios"]) > 0
    assert data["total_votos_estado"] > 0


def test_gabinete_liderancas_multi_tenancy_crud(client: TestClient):
    """Testa o isolamento de gabinete e operações CRUD completas via JWT (tenant_id no token)."""
    tenantA = str(uuid.uuid4())
    tenantB = str(uuid.uuid4())

    # 1. Falha sem autenticação
    failResponse = client.post(
        "/api/v1/gabinete/liderancas",
        json={"nm_completo": "Liderança Sem Tenant"}
    )
    assert failResponse.status_code == 401

    # 2. Cadastro no Tenant A
    createResponse = client.post(
        "/api/v1/gabinete/liderancas",
        headers=bearerHeader(tenantA),
        json={
            "nm_completo": "Liderança Comunitária Porto Alegre",
            "nr_telefone": "51999998888",
            "ds_email": "lider@portoalegre.org",
            "tp_influencia": "Comunitária",
            "cd_ibge_7": "4314902"
        }
    )
    assert createResponse.status_code == 201
    createdData = createResponse.json()
    leadershipId = createdData["id_lideranca"]
    assert createdData["tenant_id"] == tenantA
    assert createdData["nm_completo"] == "Liderança Comunitária Porto Alegre"

    # 3. Listagem no Tenant A (deve retornar 1 registro)
    listAResponse = client.get(
        "/api/v1/gabinete/liderancas",
        headers=bearerHeader(tenantA)
    )
    assert listAResponse.status_code == 200
    assert len(listAResponse.json()) >= 1

    # 4. Listagem no Tenant B (isolamento estrito: deve retornar 0 registros)
    listBResponse = client.get(
        "/api/v1/gabinete/liderancas",
        headers=bearerHeader(tenantB)
    )
    assert listBResponse.status_code == 200
    assert len(listBResponse.json()) == 0

    # 5. Tentativa do Tenant B de acessar liderança do Tenant A (deve retornar 404)
    crossTenantResponse = client.get(
        f"/api/v1/gabinete/liderancas/{leadershipId}",
        headers=bearerHeader(tenantB)
    )
    assert crossTenantResponse.status_code == 404

    # 6. Atualização no Tenant A
    updateResponse = client.put(
        f"/api/v1/gabinete/liderancas/{leadershipId}",
        headers=bearerHeader(tenantA),
        json={"tp_influencia": "Empresarial"}
    )
    assert updateResponse.status_code == 200
    assert updateResponse.json()["tp_influencia"] == "Empresarial"

    # 7. Exclusão no Tenant A
    deleteResponse = client.delete(
        f"/api/v1/gabinete/liderancas/{leadershipId}",
        headers=bearerHeader(tenantA)
    )
    assert deleteResponse.status_code == 204
