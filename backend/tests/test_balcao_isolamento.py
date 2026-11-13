"""[BAL-03] Isolamento entre gabinetes nas rotas internas do Balcão (Issue #39, DOC_012 §1).

O gabinete B nunca lê nem altera dado do gabinete A. Toda rota com id devolve 404 para o B (sem revelar
que o registro existe) e o registro do A fica como estava. As rotas exigem login, a conta da plataforma
(super_admin) não acessa dados de gabinete (ADR 039) e escrever exige papel admin ou operador; portais
são só do admin. O gabinete é sempre o do usuário autenticado (current_user.tenant_id).
"""
import uuid

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limit import RateLimiter
from tests.balcao_apoio import (
    ANEXAR, ANEXO, CAIXA, DESCARTAR, EFETIVAR, ENTRADA, GRAFO, PDF, PORTAIS, RESOLVER, REVOGAR, TIMELINE,
    consultar, efetivar, enviarEntrada, novoGabinete, pngValido, rotaRegistrada, url, usuarioDoGabinete,
)
from tests.test_sprint2_endpoints import bearerHeader


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


@pytest.fixture(scope="module")
def gabinetes(client):
    """Gabinete A com entrada pendente, entrada efetivada (atendido e atendimento), anexo e portal.
    Gabinete B com o seu próprio portal e entrada."""
    A, B = novoGabinete(client), novoGabinete(client)
    textoA = f"Entrada sigilosa do gabinete A {uuid.uuid4()}"
    nomeA = f"Atendido Sigiloso {uuid.uuid4().hex[:8]}"
    entradaPendente = enviarEntrada(client, A, textoA)
    entradaEfetivada = enviarEntrada(client, A, f"Outra entrada do A {uuid.uuid4()}")
    efetivacao = efetivar(client, A, entradaEfetivada, nome=nomeA).json()
    anexo = client.post(url(ANEXAR, id=efetivacao["atendimento_id"]), headers=A["headers"],
                        files={"anexo": ("evidencia.pdf", PDF, "application/pdf")})
    assert anexo.status_code == 201, anexo.text
    enviarEntrada(client, B, f"Entrada do gabinete B {uuid.uuid4()}")
    return {
        "A": A, "B": B, "textoA": textoA, "nomeA": nomeA,
        "entradaA": entradaPendente, "atendidoA": efetivacao["atendido_id"],
        "atendimentoA": efetivacao["atendimento_id"], "protocoloA": efetivacao["protocolo"],
        "anexoA": anexo.json()["id"], "portalA": A["portal"],
    }


@pytest.fixture(autouse=True)
def rotasExistem():
    for metodo, rota in [("GET", CAIXA), ("GET", ENTRADA), ("POST", EFETIVAR), ("POST", DESCARTAR),
                         ("GET", TIMELINE), ("GET", ANEXO), ("POST", PORTAIS), ("POST", REVOGAR),
                         ("POST", ANEXAR), ("POST", RESOLVER), ("GET", GRAFO)]:
        assert rotaRegistrada(metodo, rota), f"{metodo} {rota} não está registrada"


# --- Caixa, timeline e grafo -----------------------------------------------------------------

def test_dono_ve_a_propria_entrada_na_caixa(client, gabinetes):
    resposta = client.get(CAIXA, headers=gabinetes["A"]["headers"])
    assert resposta.status_code == 200, resposta.text
    assert gabinetes["entradaA"] in resposta.text


def test_caixa_do_b_nao_contem_a_entrada_do_a(client, gabinetes):
    resposta = client.get(CAIXA, headers=gabinetes["B"]["headers"])
    assert resposta.status_code == 200, resposta.text
    assert gabinetes["entradaA"] not in resposta.text
    assert gabinetes["textoA"] not in resposta.text


def test_filtro_de_status_e_aplicado_dentro_do_gabinete(client, gabinetes):
    pendentes = client.get(CAIXA + "?status=PENDENTE", headers=gabinetes["A"]["headers"])
    assert pendentes.status_code == 200
    assert {e["status"] for e in pendentes.json()} == {"PENDENTE"}
    assert client.get(CAIXA + "?status=qualquer", headers=gabinetes["A"]["headers"]).status_code == 422


def test_dono_le_a_timeline_do_proprio_atendido(client, gabinetes):
    resposta = client.get(url(TIMELINE, atendido_id=gabinetes["atendidoA"]), headers=gabinetes["A"]["headers"])
    assert resposta.status_code == 200, resposta.text
    assert gabinetes["protocoloA"] in resposta.text


def test_grafo_do_b_nao_contem_dados_do_a(client, gabinetes):
    do_a = client.get(GRAFO, headers=gabinetes["A"]["headers"])
    assert do_a.status_code == 200, do_a.text
    assert gabinetes["nomeA"] in do_a.text
    do_b = client.get(GRAFO, headers=gabinetes["B"]["headers"])
    assert do_b.status_code == 200
    for sigiloso in (gabinetes["nomeA"], gabinetes["atendidoA"], gabinetes["protocoloA"]):
        assert sigiloso not in do_b.text


# --- Toda rota com id: 404 para o B e o registro do A intacto ---------------------------------

def tentativas(g):
    """(nome, método, url, argumentos do request) de cada rota com id, atacando um registro do A."""
    return [
        ("entrada_por_id", "GET", url(ENTRADA, id=g["entradaA"]), {}),
        ("efetivar", "POST", url(EFETIVAR, id=g["entradaA"]), {"json": {"resumo": "x", "nome": "Fulano"}}),
        ("descartar", "POST", url(DESCARTAR, id=g["entradaA"]), {"json": {"motivo": "x"}}),
        ("timeline", "GET", url(TIMELINE, atendido_id=g["atendidoA"]), {}),
        ("baixar_anexo", "GET", url(ANEXO, id=g["anexoA"]), {}),
        ("revogar_portal", "POST", url(REVOGAR, id=g["portalA"]), {}),
        ("anexar_ao_atendimento", "POST", url(ANEXAR, id=g["atendimentoA"]),
         {"files": {"anexo": ("a.png", pngValido(), "image/png")}}),
        ("resolver", "POST", url(RESOLVER, id=g["atendimentoA"]),
         {"json": {"despacho": "x", "evidencia_anexo_id": str(uuid.uuid4())}}),
    ]


NOMES = ["entrada_por_id", "efetivar", "descartar", "timeline", "baixar_anexo", "revogar_portal",
         "anexar_ao_atendimento", "resolver"]


@pytest.mark.parametrize("nome", NOMES)
def test_rota_com_id_de_outro_gabinete_devolve_404_sem_vazar(client, gabinetes, nome):
    _, metodo, rota, args = next(t for t in tentativas(gabinetes) if t[0] == nome)
    resposta = client.request(metodo, rota, headers=gabinetes["B"]["headers"], **args)
    assert resposta.status_code == 404, resposta.text
    for sigiloso in (gabinetes["textoA"], gabinetes["nomeA"], gabinetes["protocoloA"]):
        assert sigiloso not in resposta.text


@pytest.mark.parametrize("nome", NOMES)
def test_rota_com_id_inexistente_responde_igual_a_de_outro_gabinete(client, gabinetes, nome):
    """Não há como sondar ids: id de outro gabinete e id que não existe devolvem a mesma resposta."""
    _, metodo, rota, args = next(t for t in tentativas(gabinetes) if t[0] == nome)
    deOutro = client.request(metodo, rota, headers=gabinetes["B"]["headers"], **args)
    ids = {gabinetes["entradaA"], gabinetes["atendidoA"], gabinetes["anexoA"], gabinetes["portalA"],
           gabinetes["atendimentoA"]}
    rotaInexistente = rota
    for existente in ids:
        rotaInexistente = rotaInexistente.replace(existente, str(uuid.uuid4()))
    inexistente = client.request(metodo, rotaInexistente, headers=gabinetes["B"]["headers"], **args)
    assert deOutro.status_code == inexistente.status_code == 404

    def corpo(r):
        j = r.json()
        j.pop("instance", None)
        return j
    assert corpo(deOutro) == corpo(inexistente)


def test_tentativas_do_b_deixam_os_registros_do_a_intactos(client, gabinetes):
    for _, metodo, rota, args in tentativas(gabinetes):
        client.request(metodo, rota, headers=gabinetes["B"]["headers"], **args)
    entrada = consultar("SELECT status, texto_original FROM tb_balcao_entradas WHERE id = $1",
                        uuid.UUID(gabinetes["entradaA"]))[0]
    assert entrada["status"] == "PENDENTE" and entrada["texto_original"] == gabinetes["textoA"]
    assert consultar("SELECT ativo FROM tb_balcao_portais WHERE id = $1", uuid.UUID(gabinetes["portalA"]))[0]["ativo"]
    assert consultar("SELECT 1 FROM tb_balcao_resolucoes WHERE atendimento_id = $1",
                     uuid.UUID(gabinetes["atendimentoA"])) == []
    assert len(consultar("SELECT 1 FROM tb_balcao_anexos WHERE atendimento_id = $1",
                         uuid.UUID(gabinetes["atendimentoA"]))) == 1


# --- Sessão e papel ---------------------------------------------------------------------------

def rotasInternas():
    id_ = str(uuid.uuid4())
    return [
        ("GET", CAIXA), ("GET", url(ENTRADA, id=id_)), ("POST", url(EFETIVAR, id=id_)),
        ("POST", url(DESCARTAR, id=id_)), ("GET", url(TIMELINE, atendido_id=id_)), ("GET", url(ANEXO, id=id_)),
        ("POST", PORTAIS), ("POST", url(REVOGAR, id=id_)), ("POST", url(ANEXAR, id=id_)),
        ("POST", url(RESOLVER, id=id_)), ("GET", GRAFO),
    ]


@pytest.mark.parametrize("metodo,rota", rotasInternas())
def test_rotas_internas_exigem_login(client, metodo, rota):
    client.cookies.clear()
    assert client.request(metodo, rota).status_code == 401


@pytest.mark.parametrize("metodo,rota", rotasInternas())
def test_conta_da_plataforma_nao_acessa_dados_do_gabinete(client, metodo, rota):
    headers = bearerHeader(str(uuid.uuid4()), role="super_admin")
    assert client.request(metodo, rota, headers=headers).status_code == 403


ESCRITA = [
    ("POST", lambda i: url(EFETIVAR, id=i), {"json": {"resumo": "x", "nome": "F"}}),
    ("POST", lambda i: url(DESCARTAR, id=i), {"json": {"motivo": "x"}}),
    ("POST", lambda i: url(ANEXAR, id=i), {"files": {"anexo": ("a.png", pngValido(), "image/png")}}),
    ("POST", lambda i: url(RESOLVER, id=i), {"json": {"despacho": "x"}}),
]


@pytest.mark.parametrize("metodo,rota,args", ESCRITA, ids=["efetivar", "descartar", "anexar", "resolver"])
def test_leitor_nao_escreve_no_balcao(client, gabinetes, metodo, rota, args):
    leitor = usuarioDoGabinete(gabinetes["A"], "leitor")
    assert client.request(metodo, rota(gabinetes["entradaA"]), headers=leitor, **args).status_code == 403


def test_portais_sao_so_do_admin(client, gabinetes):
    operador = usuarioDoGabinete(gabinetes["A"], "operador")
    assert client.post(PORTAIS, headers=operador).status_code == 403
    assert client.post(url(REVOGAR, id=gabinetes["portalA"]), headers=operador).status_code == 403
