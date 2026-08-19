import uuid
import logging
from typing import List, Optional
from fastapi import HTTPException, status
import asyncpg
from app.repositories.cabinet_repository import CabinetRepository
from app.schemas.leadership import (
    LiderancaCreate,
    LiderancaUpdate,
    LiderancaResponse
)

logger = logging.getLogger("CabinetService")


class CabinetService:
    """Serviço de gestão de Gabinete Digital e inteligência política com Multi-Tenancy."""

    @staticmethod
    async def createLeadership(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: LiderancaCreate
    ) -> LiderancaResponse:
        """Cria uma nova liderança política no gabinete isolado pelo tenantId."""
        logger.info(f"Cadastrando nova liderança '{payload.nm_completo}' no gabinete {tenantId}...")
        createdRecord = await CabinetRepository.createLeadership(connection, tenantId, payload)
        return LiderancaResponse(**createdRecord)

    @staticmethod
    async def listLeaderships(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        ibgeCode: Optional[str] = None,
        influenceCategory: Optional[str] = None,
        isActive: Optional[bool] = None
    ) -> List[LiderancaResponse]:
        """Lista todas as lideranças vinculadas ao gabinete do tenantId."""
        records = await CabinetRepository.listLeaderships(
            connection=connection,
            tenantId=tenantId,
            ibgeCode=ibgeCode,
            influenceCategory=influenceCategory,
            isActive=isActive
        )
        return [LiderancaResponse(**record) for record in records]

    @staticmethod
    async def getLeadershipById(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        leadershipId: uuid.UUID
    ) -> LiderancaResponse:
        """Busca uma liderança garantindo estritamente a pertença ao tenantId."""
        record = await CabinetRepository.getLeadershipById(connection, tenantId, leadershipId)
        if not record:
            logger.warning(f"Liderança {leadershipId} não localizada no gabinete {tenantId}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Liderança com ID '{leadershipId}' não encontrada para este Gabinete."
            )
        return LiderancaResponse(**record)

    @staticmethod
    async def updateLeadership(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        leadershipId: uuid.UUID,
        payload: LiderancaUpdate
    ) -> LiderancaResponse:
        """Atualiza dados cadastrais de uma liderança no gabinete."""
        # Validação prévia de existência
        await CabinetService.getLeadershipById(connection, tenantId, leadershipId)

        updatedRecord = await CabinetRepository.updateLeadership(connection, tenantId, leadershipId, payload)
        if not updatedRecord:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Não foi possível atualizar a liderança informada."
            )
        return LiderancaResponse(**updatedRecord)

    @staticmethod
    async def deleteLeadership(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        leadershipId: uuid.UUID
    ) -> None:
        """Exclui uma liderança garantindo isolamento por tenantId."""
        # Validação prévia de existência
        await CabinetService.getLeadershipById(connection, tenantId, leadershipId)

        deleted = await CabinetRepository.deleteLeadership(connection, tenantId, leadershipId)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha ao remover a liderança solicitada."
            )
        logger.info(f"Liderança {leadershipId} removida com sucesso do gabinete {tenantId}.")
