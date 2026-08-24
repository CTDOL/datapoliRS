import csv
import io
import logging
import uuid
from typing import Any, Dict
from fastapi import HTTPException, status
import asyncpg
from app.repositories.tenant_repository import TenantRepository
from app.schemas.tenant import TenantProfileResponse, TenantProfileUpdate

logger = logging.getLogger("TenantService")


class TenantService:
    """Serviço do perfil do mandato e exportação de dados do gabinete."""

    @staticmethod
    async def getProfile(connection: asyncpg.Connection, tenantId: uuid.UUID) -> TenantProfileResponse:
        record = await TenantRepository.getProfile(connection, tenantId)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gabinete não encontrado.")
        return TenantProfileResponse(**record)

    @staticmethod
    async def updateProfile(
        connection: asyncpg.Connection, tenantId: uuid.UUID, payload: TenantProfileUpdate
    ) -> TenantProfileResponse:
        updatedRecord = await TenantRepository.updateProfile(connection, tenantId, payload)
        if not updatedRecord:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gabinete não encontrado.")
        logger.info(f"Perfil do mandato atualizado para o tenant {tenantId}.")
        return TenantProfileResponse(**updatedRecord)

    @staticmethod
    async def getFormOptions(connection: asyncpg.Connection) -> Dict[str, Any]:
        return await TenantRepository.getFormOptions(connection)

    @staticmethod
    async def exportGabineteData(connection: asyncpg.Connection, tenantId: uuid.UUID) -> str:
        """Gera um CSV (com BOM UTF-8, compatível com Excel PT-BR) com as lideranças
        e emendas do gabinete, em seções separadas dentro do mesmo arquivo."""
        leaderships = await TenantRepository.exportLeaderships(connection, tenantId)
        amendments = await TenantRepository.exportAmendments(connection, tenantId)

        buffer = io.StringIO()

        buffer.write("LIDERANCAS\n")
        if leaderships:
            writer = csv.DictWriter(buffer, fieldnames=list(leaderships[0].keys()))
            writer.writeheader()
            writer.writerows(leaderships)
        buffer.write("\n")

        buffer.write("EMENDAS ORCAMENTARIAS\n")
        if amendments:
            writer = csv.DictWriter(buffer, fieldnames=list(amendments[0].keys()))
            writer.writeheader()
            writer.writerows(amendments)

        return "﻿" + buffer.getvalue()
