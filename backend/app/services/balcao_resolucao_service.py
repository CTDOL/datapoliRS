import uuid
from typing import Any, Dict
import asyncpg
from fastapi import status
from app.core.exceptions import DomainException
from app.repositories.balcao_repository import BalcaoRepository
from app.schemas.balcao import ResolverRequest
from app.schemas.user import UserInDB

DESPACHO_MAXIMO = 5000


class BalcaoResolucaoService:
    """Resolução do atendimento: exige despacho e uma evidência do mesmo gabinete e do mesmo atendimento."""

    @staticmethod
    async def resolver(connection: asyncpg.Connection, usuario: UserInDB, atendimentoId: uuid.UUID,
                       dados: ResolverRequest) -> Dict[str, Any]:
        tenantId = usuario.tenant_id
        # Primeiro o atendimento: de outro gabinete é 404, antes de qualquer validação do corpo.
        if await BalcaoRepository.obterAtendimento(connection, tenantId, atendimentoId) is None:
            raise DomainException("Atendimento não encontrado.", status.HTTP_404_NOT_FOUND, "Não encontrado")

        despacho = (dados.despacho or "").strip()
        if not despacho or len(despacho) > DESPACHO_MAXIMO:
            raise DomainException(f"Informe o despacho, com até {DESPACHO_MAXIMO} caracteres.",
                                  status.HTTP_422_UNPROCESSABLE_ENTITY, "Resolução inválida")
        if dados.evidencia_anexo_id is None:
            raise DomainException("Informe a evidência (anexo do atendimento).",
                                  status.HTTP_422_UNPROCESSABLE_ENTITY, "Resolução inválida")
        # Anexo de outro gabinete, de outro atendimento ou inexistente: a mesma resposta.
        evidencia = await BalcaoRepository.obterAnexoDoAtendimento(
            connection, tenantId, dados.evidencia_anexo_id, atendimentoId
        )
        if evidencia is None:
            raise DomainException("A evidência deve ser um anexo deste atendimento.",
                                  status.HTTP_422_UNPROCESSABLE_ENTITY, "Resolução inválida")
        return await BalcaoRepository.criarResolucao(
            connection, tenantId, atendimentoId, despacho, evidencia["id"], usuario.id
        )
