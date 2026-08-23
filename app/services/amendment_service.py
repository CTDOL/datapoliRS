import uuid
import logging
from typing import Optional
from fastapi import HTTPException, status
import asyncpg
import math
from app.repositories.amendment_repository import AmendmentRepository
from app.schemas.budget_amendment import (
    EmendaCreate,
    EmendaUpdate,
    EmendaResponse,
    EmendaPageResponse,
    EmendaKpis,
)

logger = logging.getLogger("AmendmentService")


class AmendmentService:
    """Serviço de gestão de Emendas Orçamentárias com Multi-Tenancy."""

    @staticmethod
    async def createAmendment(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: EmendaCreate
    ) -> EmendaResponse:
        """Cria uma nova emenda orçamentária no gabinete isolado pelo tenantId."""
        logger.info(f"Cadastrando nova emenda '{payload.nr_emenda or '(sem número)'}' no gabinete {tenantId}...")
        createdRecord = await AmendmentRepository.createAmendment(connection, tenantId, payload)
        return EmendaResponse(**createdRecord)

    @staticmethod
    async def listAmendments(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        ibgeCode: Optional[str] = None,
        anoExercicio: Optional[int] = None,
        tpSituacao: Optional[str] = None,
        searchTerm: Optional[str] = None,
        page: int = 1,
        pageSize: int = 50
    ) -> EmendaPageResponse:
        """Lista as emendas do gabinete do tenantId, paginadas."""
        records, total = await AmendmentRepository.listAmendments(
            connection=connection,
            tenantId=tenantId,
            ibgeCode=ibgeCode,
            anoExercicio=anoExercicio,
            tpSituacao=tpSituacao,
            searchTerm=searchTerm,
            page=page,
            pageSize=pageSize
        )
        return EmendaPageResponse(
            items=[EmendaResponse(**record) for record in records],
            total=total,
            page=page,
            page_size=pageSize,
            total_pages=math.ceil(total / pageSize) if total > 0 else 0
        )

    @staticmethod
    async def getAmendmentById(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        amendmentId: uuid.UUID
    ) -> EmendaResponse:
        """Busca uma emenda garantindo estritamente a pertença ao tenantId."""
        record = await AmendmentRepository.getAmendmentById(connection, tenantId, amendmentId)
        if not record:
            logger.warning(f"Emenda {amendmentId} não localizada no gabinete {tenantId}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Emenda com ID '{amendmentId}' não encontrada para este Gabinete."
            )
        return EmendaResponse(**record)

    @staticmethod
    async def updateAmendment(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        amendmentId: uuid.UUID,
        payload: EmendaUpdate
    ) -> EmendaResponse:
        """Atualiza dados de uma emenda no gabinete."""
        await AmendmentService.getAmendmentById(connection, tenantId, amendmentId)

        updatedRecord = await AmendmentRepository.updateAmendment(connection, tenantId, amendmentId, payload)
        if not updatedRecord:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Não foi possível atualizar a emenda informada."
            )
        return EmendaResponse(**updatedRecord)

    @staticmethod
    async def deleteAmendment(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        amendmentId: uuid.UUID
    ) -> None:
        """Exclui uma emenda garantindo isolamento por tenantId."""
        await AmendmentService.getAmendmentById(connection, tenantId, amendmentId)

        deleted = await AmendmentRepository.deleteAmendment(connection, tenantId, amendmentId)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha ao remover a emenda solicitada."
            )
        logger.info(f"Emenda {amendmentId} removida com sucesso do gabinete {tenantId}.")

    @staticmethod
    async def getKpis(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        anoExercicio: Optional[int] = None,
    ) -> EmendaKpis:
        """Retorna os indicadores agregados de emendas do gabinete do tenantId."""
        data = await AmendmentRepository.getKpis(connection, tenantId, anoExercicio)
        return EmendaKpis(**data)
