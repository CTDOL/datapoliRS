"""[BAL-01][BAL-02] Portal público do Balcão (Issue #39, DOC_012 §1, Matriz de Testes).

POST /api/v1/portal/{token}/entradas não exige login e responde 201 só com a confirmação de recebimento
(sem protocolo e sem id interno). O gabinete vem do token do portal, resolvido no banco, nunca de dado
enviado pelo cliente. Corpo: multipart/form-data com `texto` e o arquivo opcional `anexo`.

Anexos (DOC_013 §2): imagem passa pelo ImageSanitizerService; PDF vale pela assinatura %PDF- até 10 MB; o
tipo é o do conteúdo, nunca o da extensão; outro tipo devolve 415; acima de 10 MB, 413.
"""
import hashlib
import io
import re
import uuid

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app
from app.core.rate_limit import RateLimiter
from app.services.image_sanitizer_service import ImageSanitizerService
from tests.balcao_apoio import (
    PDF, PORTAL, consultar, criarPortalNoBanco, criarTenant, rotaRegistrada, url,
)


@pytest.fixture(scope="module")
def client():
    # O limitador tem o seu módulo de testes (test_balcao_limite.py); aqui fica desligado, como em
    # test_isolamento_tenant.py, para os envios do módulo não esbarrarem em 5 por minuto.
    async def semLimite(self, request: Request):
        return None

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RateLimiter, "__call__", semLimite)
        with TestClient(app) as testClient:
            yield testClient


@pytest.fixture(scope="module")
def gabinete():
    tenantId = str(uuid.uuid4())
    nome = f"Mandato Sigiloso {uuid.uuid4().hex[:8]}"
    criarTenant(tenantId, nome)
    portalId, token = criarPortalNoBanco(tenantId)
    return {"tenant": tenantId, "nome": nome, "portal": portalId, "token": token}


@pytest.fixture(autouse=True)
def rotaDoPortalExiste():
    assert rotaRegistrada("POST", PORTAL), f"POST {PORTAL} não está registrada"


def textoUnico() -> str:
    return f"Pedido de apoio ao transporte escolar {uuid.uuid4()}"


def entradasComTexto(texto: str) -> list:
    return consultar(
        "SELECT tenant_id, portal_id, status FROM tb_balcao_entradas WHERE texto_original = $1", texto
    )


def jpegComExif() -> bytes:
    imagem = Image.new("RGB", (32, 32), (10, 120, 200))
    exif = Image.Exif()
    exif[0x010F] = "Camera de Teste"
    saida = io.BytesIO()
    imagem.save(saida, format="JPEG", exif=exif)
    return saida.getvalue()


# --- BAL-01: recepção válida -----------------------------------------------------------------

def test_entrada_valida_devolve_201_e_grava_com_tenant_e_portal_do_token(client, gabinete):
    texto = textoUnico()
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": texto})
    assert resposta.status_code == 201, resposta.text
    linhas = entradasComTexto(texto)
    assert len(linhas) == 1
    assert str(linhas[0]["tenant_id"]) == gabinete["tenant"]
    assert str(linhas[0]["portal_id"]) == gabinete["portal"]
    assert linhas[0]["status"] == "PENDENTE"


def test_resposta_do_portal_e_so_a_confirmacao_sem_protocolo_nem_ids(client, gabinete):
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": textoUnico()})
    assert resposta.status_code == 201
    assert list(resposta.json().keys()) == ["mensagem"]
    assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-", resposta.text), "a resposta expõe um id interno"
    assert "BAL-" not in resposta.text


def test_tenant_enviado_pelo_cliente_e_ignorado(client, gabinete):
    outroTenant = str(uuid.uuid4())
    criarTenant(outroTenant)
    texto = textoUnico()
    resposta = client.post(
        url(PORTAL, token=gabinete["token"]),
        data={"texto": texto, "tenant_id": outroTenant},
        headers={"X-Tenant-ID": outroTenant},
    )
    assert resposta.status_code == 201, resposta.text
    assert [str(l["tenant_id"]) for l in entradasComTexto(texto)] == [gabinete["tenant"]]


def test_portal_nao_exige_login(client, gabinete):
    client.cookies.clear()
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": textoUnico()})
    assert resposta.status_code == 201, resposta.text


def test_texto_vazio_devolve_422_rfc7807_e_nao_grava(client, gabinete):
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": "   "})
    assert resposta.status_code == 422
    assert resposta.headers["content-type"].startswith("application/problem+json")


# --- BAL-02: token inválido ou revogado ------------------------------------------------------

def test_token_inexistente_devolve_404_e_nao_grava(client, gabinete):
    texto = textoUnico()
    resposta = client.post(url(PORTAL, token="token-que-nao-existe"), data={"texto": texto})
    assert resposta.status_code == 404
    assert resposta.headers["content-type"].startswith("application/problem+json")
    assert entradasComTexto(texto) == []


def test_portal_inativo_devolve_404_e_nao_grava(client, gabinete):
    _, tokenRevogado = criarPortalNoBanco(gabinete["tenant"], ativo=False)
    texto = textoUnico()
    resposta = client.post(url(PORTAL, token=tokenRevogado), data={"texto": texto})
    assert resposta.status_code == 404
    assert entradasComTexto(texto) == []


def test_404_do_portal_nao_vaza_dados_do_gabinete_e_nao_distingue_o_motivo(client, gabinete):
    _, tokenRevogado = criarPortalNoBanco(gabinete["tenant"], ativo=False)
    desconhecido = client.post(url(PORTAL, token="token-que-nao-existe"), data={"texto": textoUnico()})
    revogado = client.post(url(PORTAL, token=tokenRevogado), data={"texto": textoUnico()})
    assert desconhecido.status_code == revogado.status_code == 404
    assert {k: v for k, v in desconhecido.json().items() if k != "instance"} == \
           {k: v for k, v in revogado.json().items() if k != "instance"}
    for resposta in (desconhecido, revogado):
        assert gabinete["tenant"] not in resposta.text
        assert gabinete["nome"] not in resposta.text


# --- Anexos ----------------------------------------------------------------------------------

def anexosDaEntrada(texto: str) -> list:
    return consultar(
        """SELECT a.tenant_id, a.sha256_arquivo, a.tamanho_bytes, a.mime_type, a.caminho_arquivo
             FROM tb_balcao_anexos a JOIN tb_balcao_entradas e
               ON e.tenant_id = a.tenant_id AND e.id = a.entrada_id
            WHERE e.texto_original = $1""",
        texto,
    )


def test_pdf_pela_assinatura_e_aceito_e_gravado_como_esta(client, gabinete):
    texto = textoUnico()
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": texto},
                           files={"anexo": ("laudo.pdf", PDF, "application/pdf")})
    assert resposta.status_code == 201, resposta.text
    anexos = anexosDaEntrada(texto)
    assert len(anexos) == 1
    assert anexos[0]["mime_type"] == "application/pdf"
    assert anexos[0]["sha256_arquivo"] == hashlib.sha256(PDF).hexdigest()
    assert anexos[0]["tamanho_bytes"] == len(PDF)
    assert re.fullmatch(rf"balcao/{gabinete['tenant']}/[0-9a-f]{{32}}\.pdf", anexos[0]["caminho_arquivo"])


def test_o_tipo_vale_pelo_conteudo_e_nao_pela_extensao(client, gabinete):
    """PDF com nome de imagem é PDF; texto com nome de PDF é recusado."""
    texto = textoUnico()
    aceito = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": texto},
                         files={"anexo": ("foto.png", PDF, "image/png")})
    assert aceito.status_code == 201, aceito.text
    assert anexosDaEntrada(texto)[0]["mime_type"] == "application/pdf"

    recusado = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": textoUnico()},
                           files={"anexo": ("laudo.pdf", b"isto nao e um pdf", "application/pdf")})
    assert recusado.status_code == 415


@pytest.mark.parametrize("nome,conteudo,tipoDeclarado", [
    ("foto.jpg", b"PK\x03\x04" + b"\x00" * 64, "image/jpeg"),       # ZIP com nome de imagem
    ("programa.exe", b"MZ" + b"\x00" * 64, "application/octet-stream"),
    ("nota.txt", b"texto simples", "text/plain"),
    ("pagina.html", b"<html><script>alert(1)</script></html>", "text/html"),
])
def test_anexo_com_tipo_proibido_devolve_415_e_nao_grava_nada(client, gabinete, nome, conteudo, tipoDeclarado):
    texto = textoUnico()
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": texto},
                           files={"anexo": (nome, conteudo, tipoDeclarado)})
    assert resposta.status_code == 415, resposta.text
    assert resposta.headers["content-type"].startswith("application/problem+json")
    assert entradasComTexto(texto) == []
    assert consultar("SELECT 1 FROM tb_balcao_anexos WHERE tenant_id = $1 AND sha256_arquivo = $2",
                     gabinete["tenant"], hashlib.sha256(conteudo).hexdigest()) == []


LIMITE = 10 * 1024 * 1024


def test_pdf_de_exatamente_10_mb_e_aceito(client, gabinete):
    conteudo = PDF + b"\x00" * (LIMITE - len(PDF))
    assert len(conteudo) == LIMITE
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": textoUnico()},
                           files={"anexo": ("grande.pdf", conteudo, "application/pdf")})
    assert resposta.status_code == 201, resposta.text


def test_pdf_acima_de_10_mb_devolve_413_e_nao_grava(client, gabinete):
    conteudo = PDF + b"\x00" * (LIMITE - len(PDF) + 1)
    texto = textoUnico()
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": texto},
                           files={"anexo": ("enorme.pdf", conteudo, "application/pdf")})
    assert resposta.status_code == 413, resposta.text
    assert entradasComTexto(texto) == []


def test_anexo_de_imagem_e_gravado_pelo_conteudo_sanitizado(client, gabinete):
    original = jpegComExif()
    sanitizado = ImageSanitizerService.sanitize(original)
    assert sanitizado.conteudo != original  # o EXIF foi descartado

    texto = textoUnico()
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": texto},
                           files={"anexo": ("foto.jpg", original, "image/jpeg")})
    assert resposta.status_code == 201, resposta.text
    anexos = anexosDaEntrada(texto)
    assert len(anexos) == 1
    assert str(anexos[0]["tenant_id"]) == gabinete["tenant"]
    assert anexos[0]["sha256_arquivo"] == sanitizado.sha256
    assert anexos[0]["tamanho_bytes"] == len(sanitizado.conteudo)
    assert anexos[0]["mime_type"] == "image/jpeg"
