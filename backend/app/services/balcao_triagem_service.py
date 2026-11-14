import hashlib
import hmac
import logging
import re
import unicodedata
import uuid
from typing import Any, Dict, List, Optional
import asyncpg
from app.core.config import settings
from app.repositories.balcao_repository import BalcaoRepository
from app.repositories.geo_repository import GeoRepository

logger = logging.getLogger("BalcaoTriagemService")

# Decisão a confirmar com o operador: o DOC_012 diz "altamente similar" sem dar o número.
LIMIAR_SIMILARIDADE = 0.6
JANELA_ASSUNTO_RESOLVIDO_DIAS = 365

_CPF = re.compile(r"(?<!\d)(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})(?!\d)")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_TELEFONE = re.compile(r"(?<!\d)(?:\+?55[\s.-]?)?\(?([1-9][1-9])\)?[\s.-]?(9?\d{4})[\s.-]?(\d{4})(?!\d)")
MUNICIPIOS_HOMONIMOS_TITULO = {"capitao"}


def cpfValido(digitos: str) -> bool:
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(digitos[i]) * (tamanho + 1 - i) for i in range(tamanho))
        if (soma * 10 % 11) % 10 != int(digitos[tamanho]):
            return False
    return True


def hmacDoCpf(digitos: str) -> Optional[str]:
    """HMAC-SHA256 dos dígitos do CPF com a chave do ambiente (LGPD). Sem chave, não há hash: o CPF
    não é gravado de nenhuma forma, nem em claro."""
    chave = settings.BALCAO_CPF_HMAC_KEY
    if not chave:
        logger.warning("BALCAO_CPF_HMAC_KEY ausente: CPF do texto ignorado.")
        return None
    return hmac.new(chave.encode(), digitos.encode(), hashlib.sha256).hexdigest()


def normalizar(texto: str) -> str:
    semAcento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", semAcento.lower()).strip()


def mascararDadosPessoais(texto: str) -> str:
    """CPF, telefone e e-mail saem do texto antes de qualquer envio a provedor externo."""
    texto = _CPF.sub("[CPF]", texto)
    texto = _EMAIL.sub("[EMAIL]", texto)
    return _TELEFONE.sub("[TELEFONE]", texto)


def acharMunicipios(texto: str, municipios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Municípios citados no texto, por nome sem acento e com fronteira de palavra. Um nome contido em
    outro mais longo que também aparece na mesma posição (Santa Maria x Santa Maria do Herval) não conta.
    Municípios homônimos de patente/título (ex.: Capitão) só contam após preposição locativa ou antes de /RS ou -RS."""
    alvo = normalizar(texto)
    ocorrencias = []
    for municipio in municipios:
        nome = normalizar(municipio["nm_municipio"])
        if not nome:
            continue
        if nome in MUNICIPIOS_HOMONIMOS_TITULO:
            padrao = rf"(?:(?<![a-z0-9])(?:em|de|do|da|na|no)\s+({re.escape(nome)})(?![a-z0-9])|(?<![a-z0-9])({re.escape(nome)})(?=\s*[-/]\s*rs(?![a-z0-9])))"
            for achado in re.finditer(padrao, alvo):
                grupo = 1 if achado.group(1) is not None else 2
                ocorrencias.append((achado.start(grupo), achado.end(grupo), municipio))
        else:
            for achado in re.finditer(rf"(?<![a-z0-9]){re.escape(nome)}(?![a-z0-9])", alvo):
                ocorrencias.append((achado.start(), achado.end(), municipio))
    validos = {}
    for inicio, fim, municipio in ocorrencias:
        coberto = any(
            (i <= inicio and fim <= f and (f - i) > (fim - inicio)) for i, f, _ in ocorrencias
        )
        if not coberto:
            validos[municipio["cd_ibge_7"]] = municipio
    return list(validos.values())


def municipioUnico(texto: str, municipios: List[Dict[str, Any]]) -> Optional[str]:
    achados = acharMunicipios(texto, municipios)
    return achados[0]["cd_ibge_7"] if len(achados) == 1 else None


def extrairDados(texto: str, municipios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extração por regex, sem chamada externa. Município ambíguo ou ausente fica None (não chuta)."""
    dados: Dict[str, Any] = {}
    restante = texto

    cpf = _CPF.search(texto)
    if cpf:
        digitos = "".join(cpf.groups())
        if cpfValido(digitos):
            hashCpf = hmacDoCpf(digitos)
            if hashCpf:
                dados["cpf_hash"] = hashCpf
            restante = restante[:cpf.start()] + " " + restante[cpf.end():]

    email = _EMAIL.search(restante)
    if email:
        dados["email"] = email.group(0).lower()
        restante = restante[:email.start()] + " " + restante[email.end():]

    telefone = _TELEFONE.search(restante)
    if telefone:
        dados["telefone"] = "".join(telefone.groups())

    achados = acharMunicipios(texto, municipios)
    dados["municipio_id"] = achados[0]["cd_ibge_7"] if len(achados) == 1 else None
    if len(achados) > 1:
        ordenados = sorted(achados, key=lambda m: m["nm_municipio"])
        dados["municipios_candidatos"] = [m["nm_municipio"] for m in ordenados]
        dados["municipios_candidatos_opcoes"] = [
            {"id": m["cd_ibge_7"], "nome": m["nm_municipio"]} for m in ordenados
        ]
    return dados


class BalcaoTriagemService:
    """Triagem determinística da entrada: extração, duplicidade e alerta de assunto já resolvido."""

    @staticmethod
    async def listarMunicipios(connection: asyncpg.Connection) -> List[Dict[str, Any]]:
        return await GeoRepository.listarNomesDeMunicipios(connection)

    @staticmethod
    async def triar(connection: asyncpg.Connection, tenantId: uuid.UUID, entrada: Dict[str, Any]) -> None:
        texto = entrada["texto_original"]
        municipios = await BalcaoTriagemService.listarMunicipios(connection)
        dadosExtraidos = extrairDados(texto, municipios)
        await BalcaoRepository.gravarDadosExtraidos(
            connection, tenantId, entrada["id"], dadosExtraidos
        )

        idsJaSugeridos: List[uuid.UUID] = [entrada["id"]]
        for similarId in await BalcaoRepository.entradasComMesmoHash(
            connection, tenantId, hashlib.sha256(texto.encode()).hexdigest(), entrada["id"]
        ):
            await BalcaoRepository.criarSugestao(connection, tenantId, entrada["id"], similarId, None, 1.0, "SHA256_IDENTICO")
            idsJaSugeridos.append(similarId)

        for similar in await BalcaoRepository.entradasSimilares(
            connection, tenantId, texto, LIMIAR_SIMILARIDADE, idsJaSugeridos
        ):
            await BalcaoRepository.criarSugestao(
                connection, tenantId, entrada["id"], similar["id"], None, similar["score"], "SIMILAR_TRGM"
            )
            idsJaSugeridos.append(similar["id"])

        for contatoId in await BalcaoRepository.entradasPorContato(
            connection,
            tenantId,
            dadosExtraidos.get("telefone"),
            dadosExtraidos.get("email"),
            dadosExtraidos.get("cpf_hash"),
            idsJaSugeridos,
        ):
            await BalcaoRepository.criarSugestao(
                connection, tenantId, entrada["id"], contatoId, None, 1.0, "MESMO_CONTATO"
            )

        for resolvido in await BalcaoRepository.atendimentosResolvidosSimilares(
            connection, tenantId, texto, LIMIAR_SIMILARIDADE, JANELA_ASSUNTO_RESOLVIDO_DIAS
        ):
            await BalcaoRepository.criarSugestao(
                connection, tenantId, entrada["id"], None, resolvido["id"], resolvido["score"], "ASSUNTO_RESOLVIDO"
            )
