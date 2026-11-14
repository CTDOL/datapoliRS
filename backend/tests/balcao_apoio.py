"""Apoio dos testes de API do Balcão (Issue #39): rotas do contrato, semeadura e atalhos pela API.

A semeadura direta no banco grava de verdade (a API usa outra conexão). tb_atendimentos é
append-only, então os atendimentos criados nos testes só somem quando o banco de teste é recriado
(`make test` faz isso a cada execução).
"""
import asyncio
import hashlib
import io
import uuid

import asyncpg
from PIL import Image
from app.core.config import settings
from app.main import app
from tests.test_sprint2_endpoints import bearerHeader

PORTAL = "/api/v1/portal/{token}/entradas"
CAIXA = "/api/v1/balcao/entradas"
ENTRADA = "/api/v1/balcao/entradas/{id}"
EFETIVAR = "/api/v1/balcao/entradas/{id}/efetivar"
DESCARTAR = "/api/v1/balcao/entradas/{id}/descartar"
TIMELINE = "/api/v1/balcao/atendidos/{atendido_id}/timeline"
ANEXO = "/api/v1/balcao/anexos/{id}"
PORTAIS = "/api/v1/balcao/portais"
REVOGAR = "/api/v1/balcao/portais/{id}/revogar"
ANEXAR = "/api/v1/balcao/atendimentos/{id}/anexos"
RESOLVER = "/api/v1/balcao/atendimentos/{id}/resolver"
GRAFO = "/api/v1/balcao/grafo"

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
CPF_VALIDO = "529.982.247-25"
CHAVE_HMAC_DE_TESTE = "chave-hmac-so-para-testes"


def url(modelo: str, **valores) -> str:
    for chave, valor in valores.items():
        modelo = modelo.replace("{" + chave + "}", str(valor))
    return modelo


def rodar(coro):
    return asyncio.run(coro)


def rotaRegistrada(metodo: str, caminho: str) -> bool:
    """Sem isto, um 404 de rota inexistente passaria por um 404 de token inválido (falso verde)."""
    import re

    def forma(c):
        return re.sub(r"\{[^}]+\}", "{}", c or "")

    alvo = forma(caminho)
    metodo_lower = metodo.lower()
    paths = app.openapi().get("paths", {})
    return any(
        forma(rota) == alvo and metodo_lower in ops
        for rota, ops in paths.items()
    )


def hashDoToken(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def pngValido(cor=(10, 120, 200)) -> bytes:
    saida = io.BytesIO()
    Image.new("RGB", (16, 16), cor).save(saida, format="PNG")
    return saida.getvalue()


async def _conectar():
    return await asyncpg.connect(dsn=settings.DATABASE_URL)


def consultar(sql: str, *args) -> list:
    async def _t():
        c = await _conectar()
        try:
            return await c.fetch(sql, *args)
        finally:
            await c.close()
    return rodar(_t())


def executar(sql: str, *args) -> None:
    async def _t():
        c = await _conectar()
        try:
            await c.execute(sql, *args)
        finally:
            await c.close()
    rodar(_t())


def criarTenant(tenantId: str, nome: str = "Gabinete Balcao Teste") -> None:
    executar(
        """INSERT INTO tb_tenants (id_tenant, nm_mandato, ds_cargo_mandato)
           VALUES ($1, $2, 'Não especificado') ON CONFLICT (id_tenant) DO NOTHING""",
        tenantId, nome,
    )


def criarPortalNoBanco(tenantId: str, ativo: bool = True) -> tuple:
    """Devolve (portal_id, token em claro). Semeadura direta: a P2 do hash vale também para a rota."""
    import secrets
    token = secrets.token_urlsafe(32)

    async def _t():
        c = await _conectar()
        try:
            return str(await c.fetchval(
                "INSERT INTO tb_balcao_portais (tenant_id, token_hash, ativo) VALUES ($1, $2, $3) RETURNING id",
                tenantId, hashDoToken(token), ativo,
            ))
        finally:
            await c.close()
    return rodar(_t()), token


def criarMunicipios(*pares) -> None:
    """Municípios fictícios (sem geometria) para os testes de extração. Use removerMunicipios no fim."""
    for codigo, nome in pares:
        executar(
            """INSERT INTO tb_municipios (cd_ibge_7, nm_municipio, sg_uf) VALUES ($1, $2, 'RS')
               ON CONFLICT (cd_ibge_7) DO NOTHING""", codigo, nome,
        )


def removerMunicipios(*codigos) -> None:
    for codigo in codigos:
        executar("DELETE FROM tb_municipios WHERE cd_ibge_7 = $1", codigo)


# --- Atalhos pela API -------------------------------------------------------------------------

def novoGabinete(client, role: str = "admin") -> dict:
    """Gabinete novo com usuário admin e um portal criado pela rota (token em claro devolvido uma vez)."""
    tenant = str(uuid.uuid4())
    headers = bearerHeader(tenant, role="admin")
    criado = client.post(PORTAIS, headers=headers)
    assert criado.status_code == 201, criado.text
    return {"tenant": tenant, "headers": headers, "token": criado.json()["token"], "portal": criado.json()["id"]}


def usuarioDoGabinete(gabinete: dict, role: str) -> dict:
    """Outro usuário do mesmo gabinete, com outro papel."""
    import secrets
    from tests.test_sprint2_endpoints import createTestUser
    from app.services.auth_service import AuthService
    email = f"{role}-{secrets.token_hex(4)}@teste.datapolirs.com.br"
    createTestUser(email, gabinete["tenant"], role=role)
    token = AuthService.create_access_token(data={"sub": email, "tenant_id": gabinete["tenant"]})
    return {"Authorization": f"Bearer {token}"}


def enviarEntrada(client, gabinete: dict, texto: str, anexo: tuple = None) -> str:
    """Envia pelo portal e devolve o id da entrada, achado na caixa pelo texto único."""
    arquivos = {"anexo": anexo} if anexo else None
    resposta = client.post(url(PORTAL, token=gabinete["token"]), data={"texto": texto}, files=arquivos)
    assert resposta.status_code == 201, resposta.text
    lista = client.get(CAIXA, headers=gabinete["headers"]).json()
    return next(e["id"] for e in lista if e["texto_original"] == texto)


def efetivar(client, gabinete: dict, entradaId: str, **corpo):
    corpo.setdefault("resumo", "Pedido de apoio atendido pelo gabinete")
    corpo.setdefault("nome", "Maria da Silva")
    return client.post(url(EFETIVAR, id=entradaId), headers=gabinete["headers"], json=corpo)
