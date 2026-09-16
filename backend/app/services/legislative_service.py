import uuid
import logging
from typing import Optional
from fastapi import HTTPException, status
import asyncpg
import math
from app.repositories.legislative_repository import LegislativeRepository
from app.repositories.cabinet_repository import CabinetRepository
from app.services.legislative_sources import buscar_em_todas_fontes, obter_adaptador
from app.schemas.legislative import (
    BuscaExternaResponse,
    ProjetoLeiImport,
    ProjetoLeiResponse,
    ProjetoLeiPageResponse,
    ObservadorResponse,
)

logger = logging.getLogger("LegislativeService")


class LegislativeService:
    """Busca de proposições em fontes oficiais e gestão dos Projetos de Lei importados."""

    @staticmethod
    async def buscarExterno(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        nome: str,
    ) -> BuscaExternaResponse:
        """Agrega ALRS + Câmara + Senado, marca quais já foram importados por este
        gabinete e repassa quais fontes falharam nesta consulta."""
        resultados, fontes_com_erro = await buscar_em_todas_fontes(nome)

        importados = await LegislativeRepository.listChavesImportadas(connection, tenantId)
        chaves_importadas = {(r["fonte"], r["identificador_externo"]): r["id_projeto_lei"] for r in importados}

        for proposicao in resultados:
            chave = (proposicao.fonte, proposicao.identificador_externo)
            if chave in chaves_importadas:
                proposicao.ja_importado = True
                proposicao.id_projeto_lei = chaves_importadas[chave]

        return BuscaExternaResponse(resultados=resultados, fontes_com_erro=fontes_com_erro)

    @staticmethod
    async def importarProjetoLei(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        payload: ProjetoLeiImport,
    ) -> ProjetoLeiResponse:
        """Revalida o dado direto na fonte oficial antes de persistir — o cliente só
        informa QUAL proposição, nunca o conteúdo (ementa/situação) dela."""
        adaptador = obter_adaptador(payload.fonte)
        detalhe = await adaptador.buscar_detalhe(
            payload.identificador_externo,
            tipo=payload.tipo,
            numero=payload.numero,
            ano=payload.ano,
            autor=payload.autor,
        )
        if not detalhe:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Não foi possível confirmar essa proposição na fonte oficial. Tente buscar novamente."
            )

        dados = {
            "fonte": payload.fonte.upper(),
            "identificador_externo": payload.identificador_externo,
            "autor": payload.autor,
            **detalhe,
        }
        registro = await LegislativeRepository.importarProjetoLei(connection, tenantId, dados)
        logger.info(f"Projeto de lei {dados['fonte']}/{payload.identificador_externo} importado pro gabinete {tenantId}.")
        return ProjetoLeiResponse(**registro)

    @staticmethod
    async def listProjetosLei(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        searchTerm: Optional[str] = None,
        fonte: Optional[str] = None,
        page: int = 1,
        pageSize: int = 50,
    ) -> ProjetoLeiPageResponse:
        records, total = await LegislativeRepository.listProjetosLei(
            connection=connection, tenantId=tenantId, searchTerm=searchTerm,
            fonte=fonte, page=page, pageSize=pageSize,
        )
        return ProjetoLeiPageResponse(
            items=[ProjetoLeiResponse(**r) for r in records],
            total=total, page=page, page_size=pageSize,
            total_pages=math.ceil(total / pageSize) if total > 0 else 0,
        )

    @staticmethod
    async def getProjetoLeiById(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: uuid.UUID,
    ) -> ProjetoLeiResponse:
        record = await LegislativeRepository.getProjetoLeiById(connection, tenantId, projetoLeiId)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projeto de lei '{projetoLeiId}' não encontrado para este Gabinete."
            )
        return ProjetoLeiResponse(**record)

    @staticmethod
    async def deleteProjetoLei(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: uuid.UUID,
    ) -> None:
        await LegislativeService.getProjetoLeiById(connection, tenantId, projetoLeiId)
        deletado = await LegislativeRepository.deleteProjetoLei(connection, tenantId, projetoLeiId)
        if not deletado:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Falha ao remover o projeto de lei.")

    @staticmethod
    async def addObservador(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: uuid.UUID,
        liderancaId: uuid.UUID,
    ) -> list[ObservadorResponse]:
        await LegislativeService.getProjetoLeiById(connection, tenantId, projetoLeiId)
        lideranca = await CabinetRepository.getLeadershipById(connection, tenantId, liderancaId)
        if not lideranca:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liderança não encontrada neste gabinete.")
        await LegislativeRepository.addObservador(connection, projetoLeiId, liderancaId)
        return await LegislativeService.listObservadores(connection, tenantId, projetoLeiId)

    @staticmethod
    async def removeObservador(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: uuid.UUID,
        liderancaId: uuid.UUID,
    ) -> list[ObservadorResponse]:
        await LegislativeService.getProjetoLeiById(connection, tenantId, projetoLeiId)
        await LegislativeRepository.removeObservador(connection, projetoLeiId, liderancaId)
        return await LegislativeService.listObservadores(connection, tenantId, projetoLeiId)

    @staticmethod
    async def listObservadores(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        projetoLeiId: uuid.UUID,
    ) -> list[ObservadorResponse]:
        await LegislativeService.getProjetoLeiById(connection, tenantId, projetoLeiId)
        records = await LegislativeRepository.listObservadores(connection, projetoLeiId)
        return [ObservadorResponse(**r) for r in records]
