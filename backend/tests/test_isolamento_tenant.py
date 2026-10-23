"""Testes negativos de multi-tenancy: o gabinete B nunca enxerga nem altera dados do gabinete A.

O banco não tem Row Level Security (DOC_010, restrição 1): o isolamento depende do
filtro por tenant_id em cada service e repository. Esta suíte é a barreira que falta
para um endpoint novo que esqueça o filtro (achado 1 da auditoria de 2026-10-22).

Cada recurso de gabinete é atacado pelas quatro vias: listar, ler por id, alterar e
apagar. As referências cruzadas (tarefa ou observador do B apontando para registro do A)
também são cobertas, porque são o caminho mais fácil para um vazamento passar despercebido.
"""
import asyncio
import uuid
import asyncpg
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.repositories.legislative_repository import LegislativeRepository
from tests.test_sprint2_endpoints import bearerHeader

LIDERANCAS = "/api/v1/gabinete/liderancas"
EMENDAS = "/api/v1/gabinete/emendas"
TAREFAS = "/api/v1/gabinete/tarefas"
PROJETOS = "/api/v1/gabinete/projetos-lei"
PORTO_ALEGRE = "4314902"


def criarProjetoLei(tenantId: str) -> str:
    """Grava o PL direto pelo repositório: a rota de importação consulta a fonte oficial na rede."""
    async def _criar():
        connection = await asyncpg.connect(dsn=settings.DATABASE_URL)
        try:
            registro = await LegislativeRepository.importarProjetoLei(connection, uuid.UUID(tenantId), {
                "fonte": "ALRS",
                "identificador_externo": f"teste-isolamento-{uuid.uuid4()}",
                "tipo": "PL", "numero": "1", "ano": 2026,
                "ementa": "Projeto de teste de isolamento entre gabinetes",
                "situacao": "Em tramitação",
            })
            return str(registro["id_projeto_lei"])
        finally:
            await connection.close()
    return asyncio.run(_criar())


def idsDe(corpo, chave: str) -> set:
    """Aceita lista simples ou envelope paginado ({"items": [...]})."""
    itens = corpo["items"] if isinstance(corpo, dict) else corpo
    return {str(item[chave]) for item in itens}


@pytest.fixture(scope="module")
def client():
    # A suíte faz ~80 requisições em 3 s; o rate limiter (30/s, contador no Redis
    # compartilhado entre execuções) devolveria 429 no lugar do 404 que se quer provar.
    # Ele não é o objeto destes testes, então fica desligado só neste módulo.
    async def semLimite(self, request):
        return None

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


@pytest.fixture(scope="module")
def gabinetes(client: TestClient):
    """Gabinete A com um registro de cada recurso; gabinete B com os seus próprios PL e liderança."""
    tenantA, tenantB = str(uuid.uuid4()), str(uuid.uuid4())
    headersA, headersB = bearerHeader(tenantA), bearerHeader(tenantB)

    def criar(url, headers, payload, chave):
        resposta = client.post(url, headers=headers, json=payload)
        assert resposta.status_code == 201, resposta.text
        return str(resposta.json()[chave])

    a = {
        "lideranca": criar(LIDERANCAS, headersA, {"nm_completo": "Liderança Sigilosa do Gabinete A", "municipios": [PORTO_ALEGRE]}, "id_lideranca"),
        "emenda": criar(EMENDAS, headersA, {"ano_exercicio": 2026, "ds_objeto": "Objeto sigiloso do gabinete A", "vl_indicado": "1000000", "cd_ibge_7": PORTO_ALEGRE}, "id_emenda"),
        "projeto": criarProjetoLei(tenantA),
    }
    a["tarefa"] = criar(TAREFAS, headersA, {"titulo": "Tarefa sigilosa do gabinete A", "id_projeto_lei": a["projeto"]}, "id_tarefa")
    observador = client.post(f"{PROJETOS}/{a['projeto']}/observadores", headers=headersA, json={"id_lideranca": a["lideranca"]})
    assert observador.status_code == 200, observador.text

    b = {
        "lideranca": criar(LIDERANCAS, headersB, {"nm_completo": "Liderança do Gabinete B", "municipios": [PORTO_ALEGRE]}, "id_lideranca"),
        "projeto": criarProjetoLei(tenantB),
    }
    b["tarefa"] = criar(TAREFAS, headersB, {"titulo": "Tarefa do gabinete B"}, "id_tarefa")

    yield {"A": a, "B": b, "headersA": headersA, "headersB": headersB, "tenantB": tenantB}

    # Limpeza pelo próprio dono, para não deixar resíduo no banco de dev.
    for dono, headers in (("A", headersA), ("B", headersB)):
        registros = a if dono == "A" else b
        client.delete(f"{TAREFAS}/{registros['tarefa']}", headers=headers)
        client.delete(f"{PROJETOS}/{registros['projeto']}", headers=headers)
        client.delete(f"{LIDERANCAS}/{registros['lideranca']}", headers=headers)
    client.delete(f"{EMENDAS}/{a['emenda']}", headers=headersA)


# --- Listagens: nada do A aparece para o B -------------------------------------------

@pytest.mark.parametrize("url,chave,recurso", [
    (LIDERANCAS, "id_lideranca", "lideranca"),
    (EMENDAS, "id_emenda", "emenda"),
    (TAREFAS, "id_tarefa", "tarefa"),
    (PROJETOS, "id_projeto_lei", "projeto"),
])
def test_listagem_do_b_nao_contem_registros_do_a(client, gabinetes, url, chave, recurso):
    resposta = client.get(url, headers=gabinetes["headersB"])
    assert resposta.status_code == 200
    assert gabinetes["A"][recurso] not in idsDe(resposta.json(), chave)


# --- Leitura, alteração e exclusão por id: 404 e o registro do A intacto -------------

@pytest.mark.parametrize("url,recurso", [
    (LIDERANCAS, "lideranca"),
    (EMENDAS, "emenda"),
    (PROJETOS, "projeto"),
])
def test_leitura_por_id_de_outro_gabinete_devolve_404(client, gabinetes, url, recurso):
    resposta = client.get(f"{url}/{gabinetes['A'][recurso]}", headers=gabinetes["headersB"])
    assert resposta.status_code == 404


@pytest.mark.parametrize("url,recurso,payload,campo,valorOriginal", [
    (LIDERANCAS, "lideranca", {"nm_completo": "Invadida pelo B"}, "nm_completo", "Liderança Sigilosa do Gabinete A"),
    (EMENDAS, "emenda", {"ds_objeto": "Invadida pelo B"}, "ds_objeto", "Objeto sigiloso do gabinete A"),
])
def test_alteracao_de_outro_gabinete_devolve_404_e_preserva_registro(client, gabinetes, url, recurso, payload, campo, valorOriginal):
    idA = gabinetes["A"][recurso]
    resposta = client.put(f"{url}/{idA}", headers=gabinetes["headersB"], json=payload)
    assert resposta.status_code == 404
    assert client.get(f"{url}/{idA}", headers=gabinetes["headersA"]).json()[campo] == valorOriginal


def test_alteracao_de_tarefa_de_outro_gabinete_devolve_404_e_preserva_registro(client, gabinetes):
    idA = gabinetes["A"]["tarefa"]
    resposta = client.put(f"{TAREFAS}/{idA}", headers=gabinetes["headersB"], json={"titulo": "Invadida pelo B"})
    assert resposta.status_code == 404
    titulos = {t["id_tarefa"]: t["titulo"] for t in client.get(TAREFAS, headers=gabinetes["headersA"]).json()}
    assert titulos[idA] == "Tarefa sigilosa do gabinete A"


@pytest.mark.parametrize("url,recurso,chave", [
    (LIDERANCAS, "lideranca", "id_lideranca"),
    (EMENDAS, "emenda", "id_emenda"),
    (TAREFAS, "tarefa", "id_tarefa"),
    (PROJETOS, "projeto", "id_projeto_lei"),
])
def test_exclusao_de_outro_gabinete_devolve_404_e_preserva_registro(client, gabinetes, url, recurso, chave):
    idA = gabinetes["A"][recurso]
    resposta = client.delete(f"{url}/{idA}", headers=gabinetes["headersB"])
    assert resposta.status_code == 404
    assert idA in idsDe(client.get(url, headers=gabinetes["headersA"]).json(), chave)


def test_sincronizar_pl_de_outro_gabinete_devolve_404(client, gabinetes):
    resposta = client.post(f"{PROJETOS}/{gabinetes['A']['projeto']}/sincronizar", headers=gabinetes["headersB"])
    assert resposta.status_code == 404


# --- Referências cruzadas: o B não pode apontar para registros do A ------------------

@pytest.mark.parametrize("campo,recurso", [
    ("id_projeto_lei", "projeto"),
    ("id_emenda", "emenda"),
    ("id_lideranca_responsavel", "lideranca"),
])
def test_tarefa_do_b_nao_pode_referenciar_registro_do_a(client, gabinetes, campo, recurso):
    payload = {"titulo": "Tarefa com referência cruzada", campo: gabinetes["A"][recurso]}
    resposta = client.post(TAREFAS, headers=gabinetes["headersB"], json=payload)
    assert resposta.status_code == 404


def test_tarefa_do_b_nao_pode_receber_responsavel_do_a_na_alteracao(client, gabinetes):
    resposta = client.put(
        f"{TAREFAS}/{gabinetes['B']['tarefa']}",
        headers=gabinetes["headersB"],
        json={"id_lideranca_responsavel": gabinetes["A"]["lideranca"]}
    )
    assert resposta.status_code == 404


def test_observadores_do_pl_do_a_sao_invisiveis_para_o_b(client, gabinetes):
    resposta = client.get(f"{PROJETOS}/{gabinetes['A']['projeto']}/observadores", headers=gabinetes["headersB"])
    assert resposta.status_code == 404


def test_b_nao_pode_vincular_lideranca_do_a_ao_proprio_pl(client, gabinetes):
    resposta = client.post(
        f"{PROJETOS}/{gabinetes['B']['projeto']}/observadores",
        headers=gabinetes["headersB"],
        json={"id_lideranca": gabinetes["A"]["lideranca"]}
    )
    assert resposta.status_code == 404


def test_b_nao_pode_remover_observador_do_pl_do_a(client, gabinetes):
    a = gabinetes["A"]
    resposta = client.delete(f"{PROJETOS}/{a['projeto']}/observadores/{a['lideranca']}", headers=gabinetes["headersB"])
    assert resposta.status_code == 404
    observadores = client.get(f"{PROJETOS}/{a['projeto']}/observadores", headers=gabinetes["headersA"]).json()
    assert a["lideranca"] in {str(o["id_lideranca"]) for o in observadores}


# --- Agregados e exportação: números e nomes do A não vazam -------------------------

def test_kpis_do_b_nao_somam_emendas_do_a(client, gabinetes):
    kpis = client.get(f"{EMENDAS}/kpis", headers=gabinetes["headersB"]).json()
    assert kpis["total_emendas"] == 0
    assert float(kpis["vl_total_indicado"]) == 0


def test_exportacao_csv_do_b_nao_contem_dados_do_a(client, gabinetes):
    resposta = client.get("/api/v1/gabinete/exportar-dados", headers=gabinetes["headersB"])
    assert resposta.status_code == 200
    assert "Liderança Sigilosa do Gabinete A" not in resposta.text
    assert "Objeto sigiloso do gabinete A" not in resposta.text


# --- Equipe: admin do A não administra usuários do B ---------------------------------

def test_admin_do_a_nao_altera_usuario_do_b(client, gabinetes):
    usuariosB = client.get("/api/v1/gabinete/usuarios", headers=gabinetes["headersB"]).json()
    idUsuarioB = usuariosB[0]["id"]
    resposta = client.patch(f"/api/v1/gabinete/usuarios/{idUsuarioB}", headers=gabinetes["headersA"], json={"is_active": False})
    assert resposta.status_code == 404
    ativos = {u["id"]: u["is_active"] for u in client.get("/api/v1/gabinete/usuarios", headers=gabinetes["headersB"]).json()}
    assert ativos[idUsuarioB] is True
