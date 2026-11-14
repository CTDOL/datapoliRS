import hashlib
import secrets
import uuid
from typing import Any, Dict, List, Optional
import asyncpg
from fastapi import status
from app.core.exceptions import DomainException
from app.repositories.balcao_repository import BalcaoRepository
from app.services.balcao_anexo_service import BalcaoAnexoService
from app.services.balcao_triagem_service import BalcaoTriagemService

TEXTO_MAXIMO = 10000
MENSAGEM_DE_RECEBIMENTO = "Recebemos a sua mensagem. O gabinete vai analisá-la."


def hashDoToken(token: str) -> str:
    """O banco guarda só o SHA-256 do token; o token em claro existe apenas na resposta que o cria."""
    return hashlib.sha256(token.encode()).hexdigest()


class BalcaoPortalService:
    """Portal público (sem login) e administração dos portais do gabinete."""

    @staticmethod
    async def receberEntrada(connection: asyncpg.Connection, token: str, texto: Optional[str],
                             conteudoAnexo: Optional[bytes]) -> str:
        # O gabinete vem do portal resolvido pelo token, nunca de dado enviado pelo cliente.
        portal = await BalcaoRepository.resolverPortalPorTokenHash(connection, hashDoToken(token))
        if portal is None:
            # Token desconhecido e portal revogado respondem igual.
            raise DomainException("Portal não encontrado.", status.HTTP_404_NOT_FOUND, "Não encontrado")
        tenantId = portal["tenant_id"]

        texto = (texto or "").strip()
        if not texto or len(texto) > TEXTO_MAXIMO:
            raise DomainException(f"Informe o texto da mensagem, com até {TEXTO_MAXIMO} caracteres.",
                                  status.HTTP_422_UNPROCESSABLE_ENTITY, "Mensagem inválida")
        # Anexo recusado derruba a entrada inteira: nada é gravado.
        anexo = BalcaoAnexoService.classificar(conteudoAnexo) if conteudoAnexo is not None else None

        async with connection.transaction():
            entrada = await BalcaoRepository.criarEntrada(
                connection, tenantId, portal["id"], texto, hashlib.sha256(texto.encode()).hexdigest()
            )
            await BalcaoTriagemService.triar(connection, tenantId, entrada)
            if anexo is not None:
                await BalcaoAnexoService.salvar(connection, tenantId, anexo, entradaId=entrada["id"])
        return MENSAGEM_DE_RECEBIMENTO

    @staticmethod
    async def criarPortal(connection: asyncpg.Connection, tenantId: uuid.UUID) -> Dict[str, Any]:
        token = secrets.token_urlsafe(32)
        portal = await BalcaoRepository.criarPortal(connection, tenantId, hashDoToken(token))
        return {**portal, "token": token}

    @staticmethod
    async def listarPortais(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[Dict[str, Any]]:
        return await BalcaoRepository.listarPortais(connection, tenantId)

    @staticmethod
    async def revogarPortal(connection: asyncpg.Connection, tenantId: uuid.UUID,
                            portalId: uuid.UUID) -> Dict[str, Any]:
        portal = await BalcaoRepository.revogarPortal(connection, tenantId, portalId)
        if portal is None:
            raise DomainException("Portal não encontrado.", status.HTTP_404_NOT_FOUND, "Não encontrado")
        return portal
