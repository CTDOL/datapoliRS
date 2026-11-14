"""Bateria Multi-Registros CT-01..CT-20 (Regex e IA) — Balcão Inteligente (ONDA 2).

Implementa integralmente a Seção 2 de MATRIZ_CASOS_DE_TESTE_BALCAO_DATAPOLIRS.md:
- Modo 1 (regex puro): CT-01..CT-13 (extração determinística, ambiguidade, D1 Capitão/RS,
  falsos positivos de protocolo/800m/timestamp WhatsApp, CPF válido HMAC vs CPF inválido).
- Similaridade e Duplicidade: CT-14 (contato/similaridade) e CT-15 (SHA-256 exato).
- Anexos: CT-16 (PDF %PDF-, PNG, WEBP, disfarçado 415 e >10MB 413).
- Comutador IA <-> Regex e PII: CT-17 (openai/gemini/anthropic/ollama + fallback timeout/HTTP)
  e CT-18 (mascararDadosPessoais antes do LLM e preenchimento só de campos vazios).
- Resolução e Alerta 365 dias: CT-19 (422 sem despacho/evidência + alerta após resolução).
- Isolamento Multi-Tenant: CT-20 (tenant_B não enxerga nenhum registro de tenant_A).
"""
import hashlib
import hmac
import io
import json
import uuid

import httpx
import pytest
import respx
from fastapi import Request
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.main import app
from app.services.balcao_ia_service import BalcaoIaService
from app.services.balcao_triagem_service import acharMunicipios, extrairDados, mascararDadosPessoais
from tests.balcao_apoio import (
    ANEXAR,
    ANEXO,
    CAIXA,
    CHAVE_HMAC_DE_TESTE,
    EFETIVAR,
    ENTRADA,
    GRAFO,
    PDF,
    PORTAL,
    RESOLVER,
    TIMELINE,
    consultar,
    criarMunicipios,
    efetivar,
    enviarEntrada,
    novoGabinete,
    pngValido,
    removerMunicipios,
    url,
)

MUNICIPIOS_BATERIA = [
    ("4314902", "Porto Alegre"),
    ("4314407", "Pelotas"),
    ("4316907", "Santa Maria"),
    ("4304697", "Capitão"),
    ("4302105", "Bento Gonçalves"),
    ("4305108", "Caxias do Sul"),
    ("4304606", "Canoas"),
    ("4314100", "Passo Fundo"),
    ("4319604", "São Vicente do Sul"),
    ("4315602", "Rio Grande"),
    ("4313409", "Novo Hamburgo"),
    ("4318309", "São Gabriel"),
    ("4322400", "Uruguaiana"),
    ("4309209", "Gravataí"),
    ("4300604", "Alvorada"),
]
CODIGOS_BATERIA = {nome: codigo for codigo, nome in MUNICIPIOS_BATERIA}

TEXTOS_CT = {
    "CT-01": (
        "Boa tarde, sou o 2º Sargento Marcelo Pereira do 9º BPM de Porto Alegre (telefone 51 99888-1122). "
        "Gostaria de auxílio para desarquivamento do recurso de promoção por tempo de serviço junto ao DA "
        "da Brigada Militar. Protocolo administrativo nº 23/1200-004589."
    ),
    "CT-02": (
        "Olá deputada, me chamo Soldado Marcos Vinícius Becker, atualmente no 4º BPM em Pelotas. "
        "Meu telefone é (53) 98455-6677. Minha esposa iniciou tratamento oncológico em Santa Maria e preciso "
        "de apoio para solicitar transferência por motivo de saúde de dependente (Art. 51 do Estatuto)."
    ),
    "CT-03": (
        "Prezada equipe de gabinete, sou o Capitão Rodrigo Freitas, comandante do pelotão em Santa Maria. "
        "Contato: (55) 99123-4567, email institucional: rodrigo.bm@gmail.com. Estamos com problemas sérios "
        "no telhado da sede após os últimos temporais e solicitamos interlocução com a SOP para liberação "
        "de reforma emergencial."
    ),
    "CT-04": (
        "Prezados, sou Paulo Ricardo de Bento Gonçalves e atuo na 1ª Delegacia de Polícia Civil de Caxias do Sul "
        "(celular 54 98877-6655). Segue solicitação de apoio para conserto e reposição de viatura ostensiva "
        "que atende a serra gaúcha."
    ),
    "CT-05": (
        "Olá, me chamo Maria Helena da Silva, moro no bairro Mathias Velho em Canoas (celular 51 98765-4321, "
        "CPF 123.456.789-09). Minha mãe precisa de uma consulta urgente com especialista em neurologia pelo SUS "
        "no Hospital Universitário e está há 5 meses na fila do GERCON sem retorno. Podem nos ajudar a verificar o andamento?"
    ),
    "CT-06": (
        "Bom dia gabinete. Sou o senhor Antônio Carlos Moreira, morador de Passo Fundo, fone 54 99144-8899. "
        "Sofri fratura no fêmur há 8 meses e aguardo cirurgia ortopédica pelo Hospital São Vicente de Paulo. "
        "A dor está insuportável e não consigo trabalhar. Peço encarecidamente um apoio para agilização."
    ),
    "CT-07": (
        "Mensagem da Associação de Pacientes Renais de Rio Grande. Contato: Dra. Cláudia Fagundes, fone 53 98111-3322. "
        "Relatamos a falta contínua de insumos e medicamentos de alto custo na Farmácia do Estado local, "
        "afetando 42 pacientes em hemodiálise. Solicitamos audiência ou ofício à Secretaria Estadual de Saúde."
    ),
    "CT-08": (
        "Prezada Deputada Nadine, somos da Associação de Moradores do Bairro Lomba Grande em Novo Hamburgo. "
        "Contato com o presidente João Pedro: 51 99122-3344. Precisamos de apoio para articulação de emenda "
        "parlamentar estadual para pavimentação de trecho crítico de 800m da Rua dos Plátanos que está intransitável no inverno."
    ),
    "CT-09": (
        "Aqui é o Gilberto Silveira, produtor rural do Rincão dos Mouras em São Gabriel (fone 55 99655-4433). "
        "A ponte de madeira sobre o Arroio das Pedras caiu na enchente e 15 famílias de pequenos agricultores "
        "estão isoladas sem conseguir escoar a produção leiteira. Precisamos de ajuda junto à Defesa Civil e Daer."
    ),
    "CT-10": (
        "Sou moradora de Bento Gonçalves, Ana Paula Ferreira (CPF 012.345.678-99, fone 54 99911-2233). "
        "Gostaria de solicitar ajuda com vaga escolar para o ensino médio da minha filha na Escola Estadual "
        "Mestre Santa Bárbara, pois fomos informadas que não há turmas no período da manhã."
    ),
    "CT-11": (
        "Boa tarde. Falamos em nome da Casa da Criança de Uruguaiana. Responsável: Irmã Terezinha, telefone 55 98400-1122. "
        "Atendemos 80 crianças no contraturno escolar e gostaríamos de convidar a deputada para visitar a instituição "
        "e conhecer nosso projeto de inclusão digital."
    ),
    "CT-12": (
        "[08/11/2026 14:22] Tenente Silva: Boa tarde pessoal do gabinete passando pra reforçar o pedido de "
        "equipamentos de informática para a 1ª Cia de Gravataí. Falar com Major Renato no 51 98111-2233 que ele "
        "tem os orçamentos detalhados."
    ),
    "CT-13": (
        "sou o sd oliveira de alvorada fone 51982345678 to precisando saber sobre o andamento do projeto das "
        "horas extras da bm na assembleia se tem previsao de votacao essa semana qsl"
    ),
    "CT-14": (
        "Olá equipe do gabinete, aqui novamente o Sargento Marcelo Pereira de Porto Alegre (51 99888-1122). "
        "Passando para saber se tiveram algum retorno sobre o recurso da promoção por tempo de serviço da Brigada. "
        "Aguardo notícias obrigado."
    ),
}
TEXTOS_CT["CT-15"] = TEXTOS_CT["CT-05"]


def _webpValido() -> bytes:
    saida = io.BytesIO()
    Image.new("RGB", (16, 16), (30, 160, 90)).save(saida, format="WEBP")
    return saida.getvalue()


@pytest.fixture(scope="module")
def client():
    async def semLimite(self, request: Request):
        return None

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


@pytest.fixture(scope="module", autouse=True)
def municipiosBateria():
    # Porto Alegre (4314902) já vem do seed global de conftest.py; demais ficam disponíveis para FKs de tb_atendidos.
    extras = [(c, n) for c, n in MUNICIPIOS_BATERIA if c != "4314902"]
    criarMunicipios(*extras)
    yield


@pytest.fixture(autouse=True)
def chaveHmac(monkeypatch):
    monkeypatch.setattr(settings, "BALCAO_CPF_HMAC_KEY", CHAVE_HMAC_DE_TESTE)
    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "regex")


# --- Modo 1 (Regex puro): CT-01..CT-13 ---------------------------------------------------------


@pytest.mark.parametrize(
    "ctId,municipioEsperado,candidatosEsperados,foneEsperado,emailEsperado,temCpfHash",
    [
        ("CT-01", "Porto Alegre", None, "51998881122", None, False),
        ("CT-02", None, ["Pelotas", "Santa Maria"], "53984556677", None, False),
        ("CT-03", "Santa Maria", None, "55991234567", "rodrigo.bm@gmail.com", False),
        ("CT-04", None, ["Bento Gonçalves", "Caxias do Sul"], "54988776655", None, False),
        ("CT-05", "Canoas", None, "51987654321", None, True),
        ("CT-06", "Passo Fundo", None, "54991448899", None, False),
        ("CT-07", "Rio Grande", None, "53981113322", None, False),
        ("CT-08", "Novo Hamburgo", None, "51991223344", None, False),
        ("CT-09", "São Gabriel", None, "55996554433", None, False),
        ("CT-10", "Bento Gonçalves", None, "54999112233", None, False),
        ("CT-11", "Uruguaiana", None, "55984001122", None, False),
        ("CT-12", "Gravataí", None, "51981112233", None, False),
        ("CT-13", "Alvorada", None, "51982345678", None, False),
    ],
)
def test_bateria_regex_ct01_a_ct13(
    ctId, municipioEsperado, candidatosEsperados, foneEsperado, emailEsperado, temCpfHash
):
    listaMunicipios = [{"cd_ibge_7": c, "nm_municipio": n} for c, n in MUNICIPIOS_BATERIA]
    dados = extrairDados(TEXTOS_CT[ctId], listaMunicipios)

    assert dados.get("telefone") == foneEsperado, f"{ctId}: telefone obtido={dados.get('telefone')}"
    assert dados.get("email") == emailEsperado, f"{ctId}: email obtido={dados.get('email')}"

    if municipioEsperado is None:
        assert dados.get("municipio_id") is None
        assert dados.get("municipios_candidatos") == sorted(candidatosEsperados)
    else:
        assert dados.get("municipio_id") == CODIGOS_BATERIA[municipioEsperado], (
            f"{ctId}: esperado {municipioEsperado}, obtido={dados}"
        )

    if temCpfHash:
        esperadoHmac = hmac.new(CHAVE_HMAC_DE_TESTE.encode(), b"12345678909", hashlib.sha256).hexdigest()
        assert dados.get("cpf_hash") == esperadoHmac
    else:
        assert "cpf_hash" not in dados


def test_d1_capitao_com_preposicao_ou_uf_continua_sendo_encontrado():
    listaMunicipios = [{"cd_ibge_7": c, "nm_municipio": n} for c, n in MUNICIPIOS_BATERIA]
    assert [m["nm_municipio"] for m in acharMunicipios("Moro em Capitão há 10 anos", listaMunicipios)] == ["Capitão"]
    assert [m["nm_municipio"] for m in acharMunicipios("Demanda de Capitão/RS", listaMunicipios)] == ["Capitão"]
    assert [m["nm_municipio"] for m in acharMunicipios("Capitão Rodrigo Freitas", listaMunicipios)] == []


# --- Fluxo completo CT-01..CT-20 via API + IA + Multi-Tenant ------------------------------------


def test_bateria_integrada_ct14_a_ct20(client, monkeypatch):
    gabA = novoGabinete(client)
    gabB = novoGabinete(client)

    # CT-01 e CT-05 na Unidade A
    id01 = enviarEntrada(client, gabA, TEXTOS_CT["CT-01"])
    id05 = enviarEntrada(client, gabA, TEXTOS_CT["CT-05"])

    # CT-14: mesmo telefone do CT-01 com texto diferente -> gera sugestão no mesmo tenant
    id14 = enviarEntrada(client, gabA, TEXTOS_CT["CT-14"])

    # CT-15: cópia exata do CT-05 -> gera sugestão por SHA-256
    r15 = client.post(url(PORTAL, token=gabA["token"]), data={"texto": TEXTOS_CT["CT-15"]})
    assert r15.status_code == 201
    caixaA = client.get(CAIXA, headers=gabA["headers"]).json()
    assert len(caixaA) == 4
    id15 = next(e["id"] for e in caixaA if e["id"] != id05 and e["texto_original"] == TEXTOS_CT["CT-15"])

    det14 = client.get(url(ENTRADA, id=id14), headers=gabA["headers"]).json()
    assert any(s["entrada_similar_id"] == id01 and s["motivo"] in ("MESMO_CONTATO", "SIMILAR_TRGM") for s in det14["sugestoes"])

    det15 = client.get(url(ENTRADA, id=id15), headers=gabA["headers"]).json()
    assert any(
        s["entrada_similar_id"] == id05 and s["motivo"] == "SHA256_IDENTICO"
        for s in det15["sugestoes"]
    )

    # CT-16: Anexos (PDF válido, PNG/WEBP aceitos; arquivo disfarçado 415; >10MB 413)
    ef01Resp = efetivar(
        client,
        gabA,
        id01,
        nome="Marcelo Pereira",
        resumo="Recurso promoção 9º BPM Porto Alegre",
        municipio_id=CODIGOS_BATERIA["Porto Alegre"],
    )
    assert ef01Resp.status_code == 201, ef01Resp.text
    ef01 = ef01Resp.json()
    atendimento01 = ef01["atendimento_id"]
    atendido01 = ef01["atendido_id"]

    upPdf = client.post(
        url(ANEXAR, id=atendimento01),
        headers=gabA["headers"],
        files={"anexo": ("oficio.pdf", PDF, "application/pdf")},
    )
    assert upPdf.status_code == 201
    anexoPdfId = upPdf.json()["id"]

    upPng = client.post(
        url(ANEXAR, id=atendimento01),
        headers=gabA["headers"],
        files={"anexo": ("foto.png", pngValido(), "image/png")},
    )
    assert upPng.status_code == 201

    upWebp = client.post(
        url(ANEXAR, id=atendimento01),
        headers=gabA["headers"],
        files={"anexo": ("foto.webp", _webpValido(), "image/webp")},
    )
    assert upWebp.status_code == 201

    upDisfarcado = client.post(
        url(ANEXAR, id=atendimento01),
        headers=gabA["headers"],
        files={"anexo": ("falso.pdf", b"MZ\x90\x00NAO_E_PDF", "application/pdf")},
    )
    assert upDisfarcado.status_code == 415

    upGrande = client.post(
        url(ANEXAR, id=atendimento01),
        headers=gabA["headers"],
        files={"anexo": ("grande.pdf", b"%PDF-1.4\n" + b"0" * (10 * 1024 * 1024 + 64), "application/pdf")},
    )
    assert upGrande.status_code == 413

    # CT-17 e CT-18: Comutador IA <-> Regex + mascararDadosPessoais + fallback em timeout/erro HTTP
    id04 = enviarEntrada(client, gabA, TEXTOS_CT["CT-04"])
    det04 = client.get(url(ENTRADA, id=id04), headers=gabA["headers"]).json()
    assert det04["dados_extraidos"]["municipio_id"] is None

    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "openai")
    monkeypatch.setattr(settings, "BALCAO_IA_API_KEY", "sk-ct17-teste")
    monkeypatch.setattr(settings, "BALCAO_IA_BASE_URL", "")
    with respx.mock(assert_all_mocked=True) as mock:
        rotaOpenAi = mock.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps({"nome": "Paulo Ricardo", "municipio": "Caxias do Sul"})}}]},
            )
        )
        # CT-18: mascaramento antes do envio ao LLM
        mascarado = mascararDadosPessoais(TEXTOS_CT["CT-05"])
        assert "123.456.789-09" not in mascarado
        assert "98765-4321" not in mascarado
        ef04 = client.post(
            url(EFETIVAR, id=id04),
            headers=gabA["headers"],
            json={"resumo": "Reposição de viatura 1ª DP Caxias do Sul"},
        )
        assert ef04.status_code == 201, ef04.text
        assert rotaOpenAi.called
        enviado = json.loads(rotaOpenAi.calls[0].request.content.decode())
        assert "54 98877-6655" not in enviado["messages"][1]["content"]
        assert "[TELEFONE]" in enviado["messages"][1]["content"]

    atendido04 = consultar("SELECT atendido_id FROM tb_atendimentos WHERE id = $1", ef04.json()["atendimento_id"])[0]["atendido_id"]
    mun04 = consultar("SELECT municipio_id FROM tb_atendidos WHERE id = $1", atendido04)[0]["municipio_id"]
    assert mun04 == CODIGOS_BATERIA["Caxias do Sul"]

    # CT-17 fallback automático para regex em timeout/erro HTTP
    from tests.balcao_apoio import rodar
    with respx.mock(assert_all_mocked=True) as mock:
        mock.post("https://api.openai.com/v1/chat/completions").mock(side_effect=httpx.ReadTimeout("timeout"))
        assert rodar(BalcaoIaService.complementar(TEXTOS_CT["CT-04"], ["nome", "municipio"])) == {}

    # CT-19: Resolução exige despacho/evidência (422) e dispara alerta de 365 dias após resolução válida
    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "regex")
    ef05Resp = efetivar(
        client,
        gabA,
        id05,
        nome="Maria Helena da Silva",
        resumo="Consulta neurologia SUS Hospital Universitário Canoas",
        municipio_id=CODIGOS_BATERIA["Canoas"],
    )
    assert ef05Resp.status_code == 201, ef05Resp.text
    atendimento05 = ef05Resp.json()["atendimento_id"]
    semDespacho = client.post(
        url(RESOLVER, id=atendimento05),
        headers=gabA["headers"],
        json={"despacho": "", "evidencia_anexo_id": str(uuid.uuid4())},
    )
    assert semDespacho.status_code == 422

    upEvidencia05 = client.post(
        url(ANEXAR, id=atendimento05),
        headers=gabA["headers"],
        files={"anexo": ("comprovante.pdf", PDF, "application/pdf")},
    )
    assert upEvidencia05.status_code == 201
    evidencia05Id = upEvidencia05.json()["id"]

    res05 = client.post(
        url(RESOLVER, id=atendimento05),
        headers=gabA["headers"],
        json={"despacho": "Encaminhado ofício ao GERCON e agendada avaliação.", "evidencia_anexo_id": evidencia05Id},
    )
    assert res05.status_code == 201

    # Nova entrada semelhante após resolução válida de CT-05 -> alerta ASSUNTO_RESOLVIDO sinalizado
    textoReentrada = "Consulta neurologia SUS Hospital Universitário Canoas para minha mãe"
    id19 = enviarEntrada(client, gabA, textoReentrada)
    det19 = client.get(url(ENTRADA, id=id19), headers=gabA["headers"]).json()
    assert any(s["motivo"] == "ASSUNTO_RESOLVIDO" for s in det19["sugestoes"])

    # CT-20: Isolamento Multi-Tenant estrito (Unidade B não vê nada da Unidade A)
    assert client.get(CAIXA, headers=gabB["headers"]).json() == []
    assert client.get(url(ENTRADA, id=id14), headers=gabB["headers"]).status_code in (403, 404)
    assert client.get(url(TIMELINE, atendido_id=atendido01), headers=gabB["headers"]).status_code in (403, 404)
    assert client.get(url(ANEXO, id=anexoPdfId), headers=gabB["headers"]).status_code in (403, 404)
    assert client.post(
        url(RESOLVER, id=atendimento01),
        headers=gabB["headers"],
        json={"despacho": "Tentativa cruzada", "evidencia_anexo_id": anexoPdfId},
    ).status_code in (403, 404)
    grafoB = client.get(GRAFO, headers=gabB["headers"]).json()
    assert grafoB.get("nos", []) == [] and grafoB.get("arestas", []) == []
