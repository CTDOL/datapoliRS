import uuid
from typing import List

import asyncpg
from fastapi import HTTPException, status

from app.repositories.produtividade_repository import ProdutividadeRepository
from app.schemas.produtividade import (
    CargaResponsavel,
    ComentarioResponse,
    ProdutividadeResponse,
    TotaisTarefas,
)


class ProdutividadeService:
    """Serviço de comentários de tarefas e painel de produtividade do gabinete."""

    @staticmethod
    async def listarComentarios(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaId: uuid.UUID,
    ) -> List[ComentarioResponse]:
        if not await ProdutividadeRepository.tarefaDoTenant(connection, tenantId, tarefaId):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarefa não encontrada para este gabinete.",
            )
        registros = await ProdutividadeRepository.listarComentarios(connection, tenantId, tarefaId)
        return [ComentarioResponse(**r) for r in registros]

    @staticmethod
    async def criarComentario(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        tarefaId: uuid.UUID,
        autorEmail: str,
        texto: str,
    ) -> ComentarioResponse:
        if not await ProdutividadeRepository.tarefaDoTenant(connection, tenantId, tarefaId):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarefa não encontrada para este gabinete.",
            )
        registro = await ProdutividadeRepository.criarComentario(
            connection, tenantId, tarefaId, autorEmail, texto.strip()
        )
        return ComentarioResponse(**registro)

    @staticmethod
    async def painelProdutividade(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
    ) -> ProdutividadeResponse:
        totais = await ProdutividadeRepository.totaisTarefas(connection, tenantId)
        carga = await ProdutividadeRepository.cargaPorResponsavel(connection, tenantId)
        return ProdutividadeResponse(
            tarefas=TotaisTarefas(**totais),
            por_responsavel=[CargaResponsavel(**c) for c in carga],
            comentarios_ultimos_7_dias=await ProdutividadeRepository.comentariosRecentes(
                connection, tenantId
            ),
            projetos_lei=await ProdutividadeRepository.contar(
                connection, tenantId, "tb_gabinete_projetos_lei"
            ),
            emendas=await ProdutividadeRepository.contar(
                connection, tenantId, "tb_gabinete_emendas"
            ),
        )

