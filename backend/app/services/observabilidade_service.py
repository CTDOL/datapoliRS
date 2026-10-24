"""Observabilidade do sistema (ADR 040): trilha de acesso, saúde, alertas simples e expurgo de 6 meses."""
import time
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
from jose import JWTError, jwt

from app.core import redis_client
from app.core.config import settings

# Operações sobre dados pessoais entram na mesma trilha (revisão de 2026-10-24, M5).
EVENTOS_DADOS = ("exportacao_dados", "lideranca_excluida", "usuario_alterado")
EVENTOS = ("login_ok", "login_falha", "acesso_negado_403") + EVENTOS_DADOS
JANELA_ALERTA_MINUTOS = 60
LIMITE_FALHAS_LOGIN = 5
JANELA_NEGADOS_MINUTOS = 10
LIMITE_NEGADOS = 20
LIMITE_EMAILS_POR_IP = 3  # várias contas tentadas a partir do mesmo IP: sinal de ataque de senha


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


async def registrar_operacao(connection: asyncpg.Connection, evento: str, request: Any,
                             usuario: Any, status_http: int) -> None:
    """Quem fez, quando e sobre qual registro: o caminho da rota leva o id do alvo."""
    ip = request.client.host if request.client else None
    await registrar(connection, evento, usuario.email, str(usuario.tenant_id), request.url.path, ip, status_http)


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


async def ips_suspeitos(connection: asyncpg.Connection) -> List[Dict[str, Any]]:
    """IPs que, na última hora, tentaram senhas demais, várias contas ou geraram muitos acessos negados."""
    linhas = await connection.fetch(
        """
        SELECT ip,
               COUNT(*) FILTER (WHERE evento = 'login_falha') AS falhas_login,
               COUNT(DISTINCT email) FILTER (WHERE evento = 'login_falha') AS emails_distintos,
               COUNT(*) FILTER (WHERE evento = 'acesso_negado_403') AS negados_403,
               MAX(created_at) AS ultimo_evento
          FROM tb_log_acesso
         WHERE ip IS NOT NULL AND created_at > now() - make_interval(mins => $1)
         GROUP BY ip
        HAVING COUNT(*) FILTER (WHERE evento = 'login_falha') >= $2
            OR COUNT(DISTINCT email) FILTER (WHERE evento = 'login_falha') >= $3
            OR COUNT(*) FILTER (WHERE evento = 'acesso_negado_403') >= $4
         ORDER BY MAX(created_at) DESC
        """,
        JANELA_ALERTA_MINUTOS, LIMITE_FALHAS_LOGIN, LIMITE_EMAILS_POR_IP, LIMITE_NEGADOS,
    )
    resultado = []
    for l in linhas:
        motivos = []
        if l["falhas_login"] >= LIMITE_FALHAS_LOGIN:
            motivos.append(f"{l['falhas_login']} senhas erradas")
        if l["emails_distintos"] >= LIMITE_EMAILS_POR_IP:
            motivos.append(f"{l['emails_distintos']} contas tentadas")
        if l["negados_403"] >= LIMITE_NEGADOS:
            motivos.append(f"{l['negados_403']} acessos negados")
        resultado.append({
            "ip": l["ip"],
            "falhas_login": l["falhas_login"],
            "emails_distintos": l["emails_distintos"],
            "negados_403": l["negados_403"],
            "ultimo_evento": l["ultimo_evento"].isoformat(),
            "motivos": motivos,
            "localizacao": localizar(l["ip"]),
            "coordenadas": coordenadas(l["ip"]),
        })
    return resultado


_leitor_geoip = None


def _leitor() -> Any:
    """Abre a base GeoLite2 uma vez. Sem caminho configurado, a localização fica desligada."""
    global _leitor_geoip
    if not settings.GEOIP_DB_PATH:
        return None
    if _leitor_geoip is None:
        import geoip2.database  # import tardio: a API sobe mesmo sem a biblioteca ou a base
        _leitor_geoip = geoip2.database.Reader(settings.GEOIP_DB_PATH)
    return _leitor_geoip


def _consultar(ip: Optional[str]) -> Any:
    """Resposta bruta da base para o IP. None para IP vazio, privado, desconhecido ou sem base."""
    if not ip:
        return None
    try:
        leitor = _leitor()
    except Exception:  # noqa: BLE001 - base ausente ou corrompida não derruba o painel
        return None
    if leitor is None:
        return None
    try:
        return leitor.city(ip)
    except Exception:  # noqa: BLE001 - IP privado (ex.: 172.22.0.1) não existe na base
        return None


def localizar(ip: Optional[str]) -> Optional[str]:
    """Cidade e país do IP pela base local. Devolve None para IP privado, desconhecido ou sem base."""
    resposta = _consultar(ip)
    if resposta is None:
        return None
    partes = [resposta.city.name, resposta.country.name]
    return ", ".join(p for p in partes if p) or None


def coordenadas(ip: Optional[str]) -> Optional[Tuple[float, float]]:
    """Latitude e longitude aproximadas do IP. None quando a base não tem o ponto."""
    resposta = _consultar(ip)
    if resposta is None or resposta.location.latitude is None or resposta.location.longitude is None:
        return None
    return resposta.location.latitude, resposta.location.longitude
