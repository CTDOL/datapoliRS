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


def createTestUser(email: str, tenantId: str, role: str = "admin") -> None:
    """Insere (ou reaproveita) um tenant e um usuário de teste em tb_users para um tenant específico.

    tb_users.tenant_id tem FK obrigatória para tb_tenants (Sprint 1) — o tenant
    precisa existir antes do INSERT do usuário, senão viola a constraint.
    Default role='admin' porque o teste genérico de CRUD (abaixo) exercita
    DELETE, que agora exige esse papel (RBAC, Sprint 2).
    """
    async def _create():
        connection = await asyncpg.connect(dsn=settings.DATABASE_URL)
        try:
            await connection.execute(
                """
                INSERT INTO tb_tenants (id_tenant, nm_mandato, ds_cargo_mandato)
                VALUES ($1, 'Tenant de Teste', 'Não especificado')
                ON CONFLICT (id_tenant) DO NOTHING
                """,
                tenantId,
            )
            await connection.execute(
                """
                INSERT INTO tb_users (tenant_id, email, hashed_password, is_active, role)
                VALUES ($1, $2, $3, TRUE, $4)
                ON CONFLICT (email) DO UPDATE SET role = $4
                """,
                tenantId, email, AuthService.get_password_hash("teste123"), role,
            )
        finally:
            await connection.close()
    asyncio.run(_create())


def bearerHeader(tenantId: str, role: str = "admin") -> dict:
    """Gera um Authorization header com um JWT válido para um usuário exclusivo do tenant informado.

    O e-mail é derivado do tenantId para garantir um usuário novo a cada execução —
    tenantId é um UUID aleatório gerado por teste, então reaproveitar um e-mail fixo
    faria o ON CONFLICT manter o tenant_id de uma execução anterior.
    """
    email = f"tenant-{tenantId}@teste.datapolirs.com.br"
    createTestUser(email, tenantId, role=role)
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


def test_eleicoes_endpoint(client: TestClient):
    """Testa a listagem de pleitos disponíveis — usada para popular seletores de ano
    dinamicamente (ex: quando os dados de 2026 forem carregados, aparecem sozinhos)."""
    response = client.get("/api/v1/eleicoes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all("ano_eleicao" in item for item in data)
    anos = [item["ano_eleicao"] for item in data]
    assert anos == sorted(anos, reverse=True)


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
        json={"nm_completo": "Liderança Sem Tenant", "municipios": ["4314902"]}
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
            "municipios": ["4314902"]
        }
    )
    assert createResponse.status_code == 201
    createdData = createResponse.json()
    leadershipId = createdData["id_lideranca"]
    assert createdData["tenant_id"] == tenantA
    assert createdData["nm_completo"] == "Liderança Comunitária Porto Alegre"
    assert createdData["municipios"][0]["cd_ibge_7"] == "4314902"

    # 3. Listagem no Tenant A (deve retornar 1 registro, envelope paginado)
    listAResponse = client.get(
        "/api/v1/gabinete/liderancas",
        headers=bearerHeader(tenantA)
    )
    assert listAResponse.status_code == 200
    listAData = listAResponse.json()
    assert listAData["total"] >= 1
    assert len(listAData["items"]) >= 1
    assert listAData["page"] == 1

    # 4. Listagem no Tenant B (isolamento estrito: deve retornar 0 registros)
    listBResponse = client.get(
        "/api/v1/gabinete/liderancas",
        headers=bearerHeader(tenantB)
    )
    assert listBResponse.status_code == 200
    listBData = listBResponse.json()
    assert listBData["total"] == 0
    assert len(listBData["items"]) == 0

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


def test_delete_lideranca_requer_papel_admin(client: TestClient):
    """RBAC (Sprint 2): operador não pode excluir liderança; admin pode."""
    tenant = str(uuid.uuid4())

    createResponse = client.post(
        "/api/v1/gabinete/liderancas",
        headers=bearerHeader(tenant, role="admin"),
        json={"nm_completo": "Liderança RBAC Teste", "municipios": ["4314902"]}
    )
    assert createResponse.status_code == 201
    leadershipId = createResponse.json()["id_lideranca"]

    # Operador autenticado no mesmo tenant: exclusão deve ser negada (403)
    operatorEmail = f"operador-{tenant}@teste.datapolirs.com.br"
    createTestUser(operatorEmail, tenant, role="operador")
    operatorToken = AuthService.create_access_token(data={"sub": operatorEmail, "tenant_id": tenant})
    operatorHeader = {"Authorization": f"Bearer {operatorToken}"}

    deniedResponse = client.delete(
        f"/api/v1/gabinete/liderancas/{leadershipId}",
        headers=operatorHeader
    )
    assert deniedResponse.status_code == 403

    # Admin do mesmo tenant: exclusão deve ser permitida (204)
    allowedResponse = client.delete(
        f"/api/v1/gabinete/liderancas/{leadershipId}",
        headers=bearerHeader(tenant, role="admin")
    )
    assert allowedResponse.status_code == 204
