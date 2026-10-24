import uuid
import logging
from typing import Optional
from fastapi import HTTPException, status
import asyncpg
from app.repositories.task_repository import TaskRepository
from app.repositories.legislative_repository import LegislativeRepository
from app.repositories.amendment_repository import AmendmentRepository
from app.repositories.cabinet_repository import CabinetRepository
from app.schemas.task import TarefaCreate, TarefaUpdate, TarefaResponse

logger = logging.getLogger("TaskService")


class TaskService:
    """Gestão de tarefas (de Projeto de Lei, de Emenda ou soltas), isolada por tenant."""

    @staticmethod
    async def _validarLiderancas(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        idsResponsaveis: Optional[list[uuid.UUID]],
        idLegado: Optional[uuid.UUID],
    ) -> None:
        """Cada liderança informada precisa existir no gabinete do usuário."""
        ids = idsResponsaveis if idsResponsaveis is not None else ([idLegado] if idLegado else [])
        for idLideranca in ids:
            lideranca = await CabinetRepository.getLeadershipById(connection, tenantId, idLideranca)
            if not lideranca:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liderança responsável não encontrada neste gabinete.")

    @staticmethod
    async def createTarefa(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: TarefaCreate,
    ) -> TarefaResponse:
        if payload.id_projeto_lei:
            pl = await LegislativeRepository.getProjetoLeiById(connection, tenantId, payload.id_projeto_lei)
            if not pl:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto de lei não encontrado neste gabinete.")
        if payload.id_emenda:
            emenda = await AmendmentRepository.getAmendmentById(connection, tenantId, payload.id_emenda)
            if not emenda:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emenda não encontrada neste gabinete.")
        await TaskService._validarLiderancas(connection, tenantId, payload.ids_responsaveis, payload.id_lideranca_responsavel)

        criada = await TaskRepository.createTarefa(connection, tenantId, payload)
        return await TaskService.getTarefaById(connection, tenantId, criada["id_tarefa"])

    @staticmethod
    async def listTarefas(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: Optional[uuid.UUID] = None,
        emendaId: Optional[uuid.UUID] = None,
    ) -> list[TarefaResponse]:
        registros = await TaskRepository.listTarefas(connection, tenantId, projetoLeiId, emendaId)
        return [TarefaResponse(**r) for r in registros]

    @staticmethod
    async def getTarefaById(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaId: uuid.UUID,
    ) -> TarefaResponse:
        registro = await TaskRepository.getTarefaById(connection, tenantId, tarefaId)
        if not registro:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada neste gabinete.")
        return TarefaResponse(**registro)

    @staticmethod
    async def updateTarefa(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaId: uuid.UUID,
        payload: TarefaUpdate,
    ) -> TarefaResponse:
        await TaskService.getTarefaById(connection, tenantId, tarefaId)
        await TaskService._validarLiderancas(connection, tenantId, payload.ids_responsaveis, payload.id_lideranca_responsavel)
        atualizada = await TaskRepository.updateTarefa(connection, tenantId, tarefaId, payload)
        if not atualizada:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não foi possível atualizar a tarefa informada.")
        return await TaskService.getTarefaById(connection, tenantId, tarefaId)

    @staticmethod
    async def deleteTarefa(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaId: uuid.UUID,
    ) -> None:
        await TaskService.getTarefaById(connection, tenantId, tarefaId)
        deletado = await TaskRepository.deleteTarefa(connection, tenantId, tarefaId)
        if not deletado:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Falha ao remover a tarefa.")
