import json
import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.balcao_ia_service import BalcaoIaService
from tests.balcao_apoio import CPF_VALIDO, novoGabinete
from tests.test_sprint2_endpoints import bearerHeader


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
async def test_provedor_regex_nao_faz_chamada_externa(monkeypatch):
    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "regex")
    with respx.mock(assert_all_mocked=True) as mock:
        resultado = await BalcaoIaService.complementar("Sou Maria de Porto Alegre", ["nome", "municipio"])
    assert resultado == {}
    assert len(mock.calls) == 0


@pytest.mark.asyncio
async def test_provedor_openai_mascara_dados_e_limpa_saida(monkeypatch):
    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "openai")
    monkeypatch.setattr(settings, "BALCAO_IA_API_KEY", "sk-teste-openai")
    monkeypatch.setattr(settings, "BALCAO_IA_MODEL", "gpt-4o-mini")
    monkeypatch.setattr(settings, "BALCAO_IA_BASE_URL", "")

    with respx.mock(assert_all_mocked=True) as mock:
        rota = mock.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps({"nome": "Maria\x00 Silva", "municipio": "Porto Alegre"})}}]},
            )
        )
        resultado = await BalcaoIaService.complementar(
            f"Meu CPF {CPF_VALIDO}, fone (51) 99999-8888, email maria@exemplo.com, moro em Porto Alegre",
            ["nome", "municipio"],
        )

    assert rota.called
    enviado = json.loads(rota.calls[0].request.content.decode())
    promptUsuario = enviado["messages"][1]["content"]
    assert CPF_VALIDO not in promptUsuario
    assert "99999-8888" not in promptUsuario
    assert "maria@exemplo.com" not in promptUsuario
    assert "[CPF]" in promptUsuario and "[TELEFONE]" in promptUsuario and "[EMAIL]" in promptUsuario
    assert "não confiável" in enviado["messages"][0]["content"].lower()
    assert resultado == {"nome": "Maria  Silva", "municipio": "Porto Alegre"}


@pytest.mark.asyncio
async def test_provedor_ollama_funciona_sem_api_key(monkeypatch):
    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "BALCAO_IA_API_KEY", "")
    monkeypatch.setattr(settings, "BALCAO_IA_MODEL", "llama3.2")
    monkeypatch.setattr(settings, "BALCAO_IA_BASE_URL", "http://127.0.0.1:11434/v1")

    with respx.mock(assert_all_mocked=True) as mock:
        rota = mock.post("http://127.0.0.1:11434/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "```json\n{\"nome\": \"João Souza\"}\n```"}}]},
            )
        )
        resultado = await BalcaoIaService.complementar("João Souza precisa de apoio", ["nome"])

    assert rota.called
    assert "Authorization" not in rota.calls[0].request.headers
    assert resultado == {"nome": "João Souza"}


@pytest.mark.asyncio
async def test_provedor_gemini_via_httpx(monkeypatch):
    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "BALCAO_IA_API_KEY", "gem-key-123")
    monkeypatch.setattr(settings, "BALCAO_IA_MODEL", "gemini-2.0-flash")
    monkeypatch.setattr(settings, "BALCAO_IA_BASE_URL", "")

    with respx.mock(assert_all_mocked=True) as mock:
        rota = mock.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent").mock(
            return_value=httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": json.dumps({"municipio": "Canoas"})}]}}]},
            )
        )
        resultado = await BalcaoIaService.complementar("Pedido de Canoas", ["municipio"])

    assert rota.called
    assert rota.calls[0].request.headers["x-goog-api-key"] == "gem-key-123"
    assert resultado == {"municipio": "Canoas"}


@pytest.mark.asyncio
async def test_provedor_anthropic_via_httpx(monkeypatch):
    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "anthropic")
    monkeypatch.setattr(settings, "BALCAO_IA_API_KEY", "ant-key-123")
    monkeypatch.setattr(settings, "BALCAO_IA_MODEL", "claude-3-5-haiku-latest")
    monkeypatch.setattr(settings, "BALCAO_IA_BASE_URL", "")

    with respx.mock(assert_all_mocked=True) as mock:
        rota = mock.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(
                200,
                json={"content": [{"type": "text", "text": json.dumps({"nome": "Ana Clara"})}]},
            )
        )
        resultado = await BalcaoIaService.complementar("Ana Clara solicitou atendimento", ["nome"])

    assert rota.called
    assert rota.calls[0].request.headers["x-api-key"] == "ant-key-123"
    assert resultado == {"nome": "Ana Clara"}


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [500, 429])
async def test_fallback_silencioso_em_erro_http_ou_sem_chave(monkeypatch, status_code):
    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "openai")
    monkeypatch.setattr(settings, "BALCAO_IA_API_KEY", "sk-teste")
    monkeypatch.setattr(settings, "BALCAO_IA_BASE_URL", "")

    with respx.mock(assert_all_mocked=True) as mock:
        mock.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(status_code, json={"error": "falha"})
        )
        resultado = await BalcaoIaService.complementar("Qualquer texto", ["nome"])
    assert resultado == {}

    monkeypatch.setattr(settings, "BALCAO_IA_API_KEY", "")
    resultadoSemChave = await BalcaoIaService.complementar("Qualquer texto", ["nome"])
    assert resultadoSemChave == {}


@pytest.mark.asyncio
async def test_fallback_silencioso_em_timeout(monkeypatch):
    monkeypatch.setattr(settings, "BALCAO_IA_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "BALCAO_IA_API_KEY", "gem-key")
    monkeypatch.setattr(settings, "BALCAO_IA_BASE_URL", "")

    with respx.mock(assert_all_mocked=True) as mock:
        mock.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent").mock(
            side_effect=httpx.ReadTimeout("timeout")
        )
        resultado = await BalcaoIaService.complementar("Qualquer texto", ["nome"])
    assert resultado == {}


def test_endpoints_comutador_ia_restritos_a_admin_e_comutacao_runtime(client):
    import uuid
    gab = novoGabinete(client)
    headersAdmin = gab["headers"]
    headersOperador = bearerHeader(str(uuid.uuid4()), role="operador")

    assert client.get("/api/v1/balcao/ia-config", headers=headersOperador).status_code == 403
    assert client.put(
        "/api/v1/balcao/ia-config",
        headers=headersOperador,
        json={"provider": "openai", "model": "gpt-4o-mini", "base_url": ""},
    ).status_code == 403

    inicial = client.get("/api/v1/balcao/ia-config", headers=headersAdmin)
    assert inicial.status_code == 200
    assert inicial.json()["provider"] == "regex"
    assert "api_key" not in inicial.json()

    invalido = client.put(
        "/api/v1/balcao/ia-config",
        headers=headersAdmin,
        json={"provider": "provedor-inexistente", "model": "", "base_url": ""},
    )
    assert invalido.status_code == 422

    comutado = client.put(
        "/api/v1/balcao/ia-config",
        headers=headersAdmin,
        json={"provider": "ollama", "model": "llama3.2", "base_url": "http://127.0.0.1:11434/v1"},
    )
    assert comutado.status_code == 200, comutado.text
    corpo = comutado.json()
    assert corpo["provider"] == "ollama"
    assert corpo["model"] == "llama3.2"
    assert corpo["base_url"] == "http://127.0.0.1:11434/v1"

    restaurado = client.put(
        "/api/v1/balcao/ia-config",
        headers=headersAdmin,
        json={"provider": "regex", "model": "", "base_url": ""},
    )
    assert restaurado.status_code == 200
    assert restaurado.json()["provider"] == "regex"


def test_chave_api_ia_gravada_cifrada_e_removida_pelo_endpoint(client):
    gab = novoGabinete(client)
    headersAdmin = gab["headers"]

    salvo = client.put(
        "/api/v1/balcao/ia-config",
        headers=headersAdmin,
        json={"provider": "cohere", "model": "", "base_url": "", "api_key": "cohere-segredo-123"},
    )
    assert salvo.status_code == 200, salvo.text
    corpo = salvo.json()
    assert corpo["provider"] == "cohere"
    assert corpo["api_key_configurada"] is True
    assert "api_key" not in corpo

    removido = client.put(
        "/api/v1/balcao/ia-config",
        headers=headersAdmin,
        json={"provider": "regex", "model": "", "base_url": "", "limpar_api_key": True},
    )
    assert removido.status_code == 200
    assert removido.json()["api_key_configurada"] is False


def test_endpoint_testar_api_ia_valida_regex_e_provedor_mockado(client):
    gab = novoGabinete(client)
    headersAdmin = gab["headers"]

    resRegex = client.post(
        "/api/v1/balcao/ia-config/testar",
        headers=headersAdmin,
        json={"provider": "regex"},
    )
    assert resRegex.status_code == 200
    assert resRegex.json()["ok"] is True
    assert resRegex.json()["provider"] == "regex"

    class ProvedorFakeTeste:
        model = "command-a-03-2025"

        async def complementar(self, pedido):
            return {"nome": "Maria Silva", "municipio": "Porto Alegre"}

    from unittest.mock import patch

    with patch("app.services.balcao_ia_service.BalcaoIaService._construirProvedor", return_value=ProvedorFakeTeste()):
        resCohere = client.post(
            "/api/v1/balcao/ia-config/testar",
            headers=headersAdmin,
            json={"provider": "cohere", "api_key": "cohere-teste"},
        )
    assert resCohere.status_code == 200
    assert resCohere.json()["ok"] is True
    assert resCohere.json()["resultado"] == {"nome": "Maria Silva", "municipio": "Porto Alegre"}
