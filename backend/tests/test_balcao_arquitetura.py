"""Regras de desenho do Balcão (Issue #39), conferidas no código-fonte e no roteamento.

Nascem do mapa do backend e dos achados do piloto de 2026-11-13:
  - o router chama só service (o achado de routers que importam repository não se repete);
  - todo SQL do repository filtra por tenant_id, inclusive INSERT e DELETE em tabela filha
    (o achado dos observadores de PL sem tenant_id no SQL não se repete);
  - balcao* não importa tasks nem acessa tb_tarefas* (DOC_013 §1);
  - todas as rotas do portal têm o limitador 5/60 s com falha fechada e nenhuma exige login;
  - todas as rotas internas exigem sessão, bloqueiam a conta da plataforma e têm RateLimiter.

A checagem de SQL é heurística: prova que a consulta cita tenant_id, não que o filtro está certo.
Quem prova o filtro são os testes de isolamento e a prova de mutação (Regra 12.4).
"""
import ast
import importlib
import re
from pathlib import Path

import pytest
from app.core.dependencies import bloquear_super_admin, get_current_user
from app.core.rate_limit import RateLimiter

RAIZ = Path(__file__).resolve().parent.parent / "app"
ROUTERS = [RAIZ / "routers" / "balcao.py", RAIZ / "routers" / "balcao_portal.py"]
SERVICES = sorted((RAIZ / "services").glob("balcao_*.py"))
REPOSITORIES = sorted((RAIZ / "repositories").glob("balcao_*.py"))
ESPERADOS = ROUTERS + [RAIZ / "repositories" / "balcao_repository.py"] + [
    RAIZ / "services" / f"balcao_{nome}_service.py"
    for nome in ("portal", "caixa", "triagem", "anexo", "resolucao", "ia", "grafo")
]

SQL = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE|WITH)\b", re.IGNORECASE)


def arvore(caminho: Path) -> ast.Module:
    assert caminho.exists(), f"{caminho.relative_to(RAIZ.parent)} não existe"
    return ast.parse(caminho.read_text(encoding="utf-8"))


def importados(caminho: Path) -> list:
    nomes = []
    for no in ast.walk(arvore(caminho)):
        if isinstance(no, ast.ImportFrom):
            nomes.append(no.module or "")
            nomes.extend(alias.name for alias in no.names)
        elif isinstance(no, ast.Import):
            nomes.extend(alias.name for alias in no.names)
    return nomes


@pytest.mark.parametrize("caminho", ESPERADOS, ids=lambda c: c.name)
def test_arquivo_do_balcao_existe(caminho):
    arvore(caminho)


@pytest.mark.parametrize("caminho", ROUTERS, ids=lambda c: c.name)
def test_router_do_balcao_nao_importa_repository(caminho):
    proibidos = [nome for nome in importados(caminho) if "repositor" in nome.lower()]
    assert proibidos == [], f"{caminho.name} importa repository: {proibidos}"


@pytest.mark.parametrize("caminho", ROUTERS + SERVICES + REPOSITORIES, ids=lambda c: c.name)
def test_balcao_nao_importa_tasks_nem_acessa_tabelas_de_tarefas(caminho):
    assert [n for n in importados(caminho) if "task" in n.lower()] == []
    assert not re.search(r"tb_(gabinete_)?tarefa", caminho.read_text(encoding="utf-8"), re.IGNORECASE)


def sqlsDo(caminho: Path) -> list:
    return [
        no.value for no in ast.walk(arvore(caminho))
        if isinstance(no, ast.Constant) and isinstance(no.value, str) and SQL.match(no.value)
    ]


def resolvePortalPeloToken(sql: str) -> bool:
    s = " ".join(sql.lower().split())
    return "from tb_balcao_portais" in s and "token_hash = $1" in s


def travaDeAdvisory(sql: str) -> bool:
    """Não lê nem grava tabela: só serializa o número do protocolo por (gabinete, ano)."""
    s = " ".join(sql.lower().split())
    return s.startswith("select pg_advisory_xact_lock(") and "tb_" not in s


def test_todo_sql_do_repository_cita_tenant_id():
    """Exceções: a consulta que resolve o portal pelo hash do token (devolve o tenant_id do portal) e o
    advisory lock do protocolo, que não toca em tabela."""
    sqls = [s for caminho in REPOSITORIES for s in sqlsDo(caminho)]
    assert sqls, "balcao_repository.py não tem nenhum SQL"
    # A consulta do portal cita tenant_id porque o devolve; o que a distingue das demais é não filtrar por ele.
    portal = [s for s in sqls if resolvePortalPeloToken(s)]
    assert len(portal) == 1, "deve haver exatamente uma consulta de resolução do portal pelo token"
    trava = [s for s in sqls if travaDeAdvisory(s)]
    assert len(trava) <= 1
    sem_filtro = [
        " ".join(s.split())[:90] for s in sqls
        if "tenant_id" not in s and s not in portal and s not in trava
    ]
    assert sem_filtro == [], f"SQL sem tenant_id: {sem_filtro}"
    # Fora a exceção do portal, todo SQL tem de FILTRAR por tenant_id, e não só citá-lo.
    sem_where = [
        " ".join(s.split())[:90] for s in sqls
        if s not in portal and s not in trava
        and not re.search(r"tenant_id\s*=\s*\$\d|\(\s*tenant_id\s*,", s, re.IGNORECASE)
    ]
    assert sem_where == [], f"SQL que cita tenant_id sem filtrá-lo ou gravá-lo: {sem_where}"


def chamadasDe(dependant) -> list:
    chamadas = []
    for dep in dependant.dependencies:
        chamadas.append(dep.call)
        chamadas.extend(chamadasDe(dep))
    return chamadas


def rotasDo(modulo: str):
    roteador = importlib.import_module(modulo).router
    rotas = [r for r in roteador.routes if hasattr(r, "dependant")]
    assert rotas, f"{modulo} não tem rotas"
    return rotas


def limitadores(chamadas) -> list:
    return [c for c in chamadas if isinstance(c, RateLimiter)]


def test_todas_as_rotas_do_portal_tem_limitador_5_por_60s_com_falha_fechada_e_nenhuma_exige_login():
    for rota in rotasDo("app.routers.balcao_portal"):
        chamadas = chamadasDe(rota.dependant)
        achados = limitadores(chamadas)
        assert len(achados) == 1, f"{rota.path} sem RateLimiter"
        limitador = achados[0]
        assert (limitador.times, limitador.seconds) == (5, 60)
        assert limitador.configKey == "balcao_portal"
        assert limitador.falhaFechada is True
        assert get_current_user not in chamadas, f"{rota.path} exige login, mas o portal é público"


def test_todas_as_rotas_internas_exigem_sessao_bloqueiam_plataforma_e_tem_limitador():
    for rota in rotasDo("app.routers.balcao"):
        chamadas = chamadasDe(rota.dependant)
        assert get_current_user in chamadas, f"{rota.path} não exige sessão"
        assert bloquear_super_admin in chamadas, f"{rota.path} não bloqueia a conta da plataforma"
        assert limitadores(chamadas), f"{rota.path} sem RateLimiter"


def test_so_o_portal_falha_fechado():
    for rota in rotasDo("app.routers.balcao"):
        assert all(not l.falhaFechada for l in limitadores(chamadasDe(rota.dependant)))
    assert RateLimiter().falhaFechada is False
