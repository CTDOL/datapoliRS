"""Observabilidade do sistema (ADR 040): trilha de acesso, saúde, alertas simples e expurgo de 6 meses."""
import time
from typing import Any, Dict, List, Optional

import asyncpg
from jose import JWTError, jwt

from app.core import redis_client
from app.core.config import settings

EVENTOS = ("login_ok", "login_falha", "acesso_negado_403")
JANELA_ALERTA_MINUTOS = 60
LIMITE_FALHAS_LOGIN = 5
JANELA_NEGADOS_MINUTOS = 10
LIMITE_NEGADOS = 20


async def registrar(connection: asyncpg.Connection, evento: str, email: Optional[str] = None,
                    tenant_id: Optional[str] = None, caminho: Optional[str] = None,
                    ip: Optional[str] = None, status_http: Optional[int] = None) -> None:
    await connection.execute(
        """
        INSERT INTO tb_log_acesso (evento, email, tenant_id, caminho, ip, status_http)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        evento, email, tenant_id, caminho, ip, status_http,
    )


def identificar_pelo_token(token: Optional[str]) -> Dict[str, Optional[str]]:
    """Lê e-mail e gabinete de um JWT válido, sem consultar o banco. Token inválido vira identificação vazia."""
    if not token:
        return {"email": None, "tenant_id": None}
    try:
        carga = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return {"email": carga.get("sub"), "tenant_id": carga.get("tenant_id")}
    except JWTError:
        return {"email": None, "tenant_id": None}


async def listar(connection: asyncpg.Connection, evento: Optional[str], limite: int) -> List[Dict[str, Any]]:
    if evento:
        linhas = await connection.fetch(
            "SELECT created_at, evento, email, tenant_id, caminho, ip, status_http FROM tb_log_acesso "
            "WHERE evento = $1 ORDER BY created_at DESC LIMIT $2", evento, limite)
    else:
        linhas = await connection.fetch(
            "SELECT created_at, evento, email, tenant_id, caminho, ip, status_http FROM tb_log_acesso "
            "ORDER BY created_at DESC LIMIT $1", limite)
    return [{**dict(l), "tenant_id": str(l["tenant_id"]) if l["tenant_id"] else None,
             "created_at": l["created_at"].isoformat()} for l in linhas]


async def saude(connection: asyncpg.Connection) -> Dict[str, Any]:
    inicio = time.perf_counter()
    try:
        await connection.fetchval("SELECT 1")
        banco = {"status": "ok", "latencia_ms": round((time.perf_counter() - inicio) * 1000, 1)}
    except Exception as erro:  # noqa: BLE001 - o painel precisa mostrar a falha, não quebrar
        banco = {"status": "erro", "detalhe": str(erro)[:200]}

    cliente = redis_client.redisClientInstance
    if cliente is None:
        cache = {"status": "indisponivel", "detalhe": "modo fallback: consultas direto no banco"}
    else:
        try:
            await cliente.ping()
            cache = {"status": "ok"}
        except Exception as erro:  # noqa: BLE001
            cache = {"status": "erro", "detalhe": str(erro)[:200]}

    return {"api": {"status": "ok", "versao": settings.API_VERSION, "ambiente": settings.ENVIRONMENT},
            "banco": banco, "cache": cache}


async def alertas(connection: asyncpg.Connection) -> List[Dict[str, str]]:
    resultado: List[Dict[str, str]] = []
    falhas = await connection.fetch(
        """
        SELECT email, COUNT(*) AS total FROM tb_log_acesso
         WHERE evento = 'login_falha' AND created_at > now() - make_interval(mins => $1)
           AND email IS NOT NULL
         GROUP BY email HAVING COUNT(*) >= $2
        """,
        JANELA_ALERTA_MINUTOS, LIMITE_FALHAS_LOGIN,
    )
    for f in falhas:
        resultado.append({"severidade": "alta", "titulo": "Tentativas de login repetidas",
                          "detalhe": f"{f['email']}: {f['total']} falhas em {JANELA_ALERTA_MINUTOS} min"})

    negados = await connection.fetchval(
        "SELECT COUNT(*) FROM tb_log_acesso WHERE evento = 'acesso_negado_403' "
        "AND created_at > now() - make_interval(mins => $1)",
        JANELA_NEGADOS_MINUTOS,
    )
    if negados >= LIMITE_NEGADOS:
        resultado.append({"severidade": "media", "titulo": "Volume de acessos negados",
                          "detalhe": f"{negados} acessos negados em {JANELA_NEGADOS_MINUTOS} min"})
    return resultado


async def expurgar(connection: asyncpg.Connection) -> int:
    """Remove registros mais antigos que o prazo de guarda e devolve quantos saíram."""
    status = await connection.execute(
        "DELETE FROM tb_log_acesso WHERE created_at < now() - interval '6 months'"
    )
    return int(status.split()[-1])
