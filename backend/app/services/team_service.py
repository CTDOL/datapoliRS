import logging
import uuid
from typing import List
from fastapi import HTTPException, status
import asyncpg
from app.repositories.user_repository import EmailAlreadyExistsError, UserRepository
from app.schemas.team import TeamMemberCreate, TeamMemberResponse, TeamMemberUpdate
from app.services.auth_service import AuthService

logger = logging.getLogger("TeamService")


class TeamService:
    """Serviço de gestão de equipe e acessos (RBAC) do gabinete."""

    @staticmethod
    async def listMembers(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[TeamMemberResponse]:
        records = await UserRepository.listByTenant(connection, tenantId)
        return [TeamMemberResponse(**r) for r in records]

    @staticmethod
    async def createMember(
        connection: asyncpg.Connection, tenantId: uuid.UUID, payload: TeamMemberCreate
    ) -> TeamMemberResponse:
        hashedPassword = AuthService.get_password_hash(payload.password)
        try:
            record = await UserRepository.createInTenant(
                connection, tenantId, payload.email, hashedPassword, payload.role
            )
        except EmailAlreadyExistsError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um usuário cadastrado com o e-mail '{payload.email}'."
            )
        logger.info(f"Usuário '{payload.email}' ({payload.role}) adicionado ao gabinete {tenantId}.")
        return TeamMemberResponse(**record)

    @staticmethod
    async def updateMember(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        currentUserId: uuid.UUID,
        targetUserId: uuid.UUID,
        payload: TeamMemberUpdate
    ) -> TeamMemberResponse:
        if targetUserId == currentUserId and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você não pode desativar a própria conta enquanto estiver autenticado."
            )

        existing = await UserRepository.getByIdAndTenant(connection, tenantId, targetUserId)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado neste gabinete.")

        hashedPassword = AuthService.get_password_hash(payload.password) if payload.password else None

        updatedRecord = await UserRepository.updateInTenant(
            connection,
            tenantId,
            targetUserId,
            role=payload.role,
            isActive=payload.is_active,
            hashedPassword=hashedPassword
        )
        if payload.password:
            logger.info(f"Senha do usuário {targetUserId} redefinida pelo administrador {currentUserId} (tenant {tenantId}).")
        return TeamMemberResponse(**updatedRecord)
