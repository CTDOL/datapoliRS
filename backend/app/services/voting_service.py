import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
import asyncpg
from app.core.config import settings
from app.core.redis_client import CacheService
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.voting_repository import VotingRepository
from app.services.system_config_service import SystemConfigService
from app.schemas.voting import (
    CandidatoBuscaItem,
    MunicipioVotacaoItem,
    VotacaoCandidatoResponse
)

logger = logging.getLogger("VotingService")

CANDIDATE_VOTES_CACHE_PREFIX = "voting:candidate"
CANDIDATE_VOTES_CACHE_TTL = 86400  # 24 Horas


class VotingService:
    """Serviço de apuração analítica, inteligência eleitoral e rankings de votação."""

    def __init__(self, candidate_repo: CandidateRepository, voting_repo: VotingRepository):
        self.candidate_repo = candidate_repo
        self.voting_repo = voting_repo

    async def searchCandidates(
        self,
        connection: asyncpg.Connection,
        searchTerm: Optional[str] = None,
        cargoCode: Optional[int] = None,
        partidoSigla: Optional[str] = None,
        candidateNumber: Optional[int] = None,
        ano: int = settings.ELECTION_YEAR,
        limit: int = 50
    ) -> List[CandidatoBuscaItem]:
        """Pesquisa candidaturas no banco de dados com filtros flexíveis."""
        candidatesRaw = await self.candidate_repo.searchCandidates(
            connection=connection,
            searchTerm=searchTerm,
            cargoCode=cargoCode,
            partidoSigla=partidoSigla,
            candidateNumber=candidateNumber,
            ano=ano,
            limit=limit
        )
        return [CandidatoBuscaItem(**candidate) for candidate in candidatesRaw]

    async def getCandidateVotesBySq(
        self,
        connection: asyncpg.Connection,
        sqCandidato: int
    ) -> VotacaoCandidatoResponse:
        """Calcula o mapa analítico de votação de um candidato a partir do seu SQ_CANDIDATO."""
        cacheKey = f"{CANDIDATE_VOTES_CACHE_PREFIX}:{sqCandidato}:votes"

        # 1. Checagem no Cache Redis
        cachedResponse = await CacheService.get(cacheKey)
        if cachedResponse:
            logger.debug(f"Retornando votação do candidato {sqCandidato} via Cache Redis.")
            return VotacaoCandidatoResponse(**cachedResponse)

        # 2. Localizar dados cadastrais do candidato
        candidateData = await self.candidate_repo.getCandidateBySq(connection, sqCandidato)
        if not candidateData:
            logger.warning(f"Candidato com SQ {sqCandidato} não localizado no banco de dados.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidatura com identificador SQ '{sqCandidato}' não foi encontrada."
            )

        # 3. Recuperar agregação de votos por município
        votesByMunicipioRaw = await self.voting_repo.getVotesByCandidateSq(connection, sqCandidato)
        
        totalVotosEstado = sum(item["votos"] for item in votesByMunicipioRaw)
        municipiosVotados = len(votesByMunicipioRaw)

        # 4. Construir itens detalhados com percentual de concentração
        distribuicaoMunicipios: List[MunicipioVotacaoItem] = []
        for row in votesByMunicipioRaw:
            votosNominais = row["votos"]
            percentual = round((votosNominais / totalVotosEstado * 100), 2) if totalVotosEstado > 0 else 0.0
            distribuicaoMunicipios.append(
                MunicipioVotacaoItem(
                    cd_tse_municipio=row["cd_tse_municipio"],
                    nm_municipio=row["nm_municipio"] or f"Município {row['cd_tse_municipio']}",
                    cd_ibge_7=row.get("cd_ibge_7"),
                    votos=votosNominais,
                    percentual_total_candidato=percentual
                )
            )

        response = VotacaoCandidatoResponse(
            sq_candidato=candidateData["sq_candidato"],
            nr_candidato=candidateData["nr_candidato"],
            nm_urna_candidato=candidateData["nm_urna_candidato"],
            nm_candidato=candidateData["nm_candidato"],
            ds_cargo=candidateData["ds_cargo"],
            sg_partido=candidateData["sg_partido"],
            cd_eleicao=candidateData["cd_eleicao"],
            total_votos_estado=totalVotosEstado,
            municipios_votados=municipiosVotados,
            distribuicao_municipios=distribuicaoMunicipios
        )

        # 5. Salvar no Cache Redis
        ttl = await SystemConfigService.getInt(connection, "cache_ttl.candidate_votes", CANDIDATE_VOTES_CACHE_TTL)
        await CacheService.set(cacheKey, response.model_dump(), ttlSeconds=ttl)
        return response

    async def getCandidateVotesByNumber(
        self,
        connection: asyncpg.Connection,
        candidateNumber: int,
        cargoCode: Optional[int] = None,
        ano: int = settings.ELECTION_YEAR
    ) -> VotacaoCandidatoResponse:
        """Localiza o candidato pelo número eleitoral e cargo e retorna seus votos."""
        candidate = await self.voting_repo.getVotesByCandidateNumberAndCargo(
            connection=connection,
            candidateNumber=candidateNumber,
            cargoCode=cargoCode,
            ano=ano
        )
        if not candidate:
            cargoMsg = f" para o cargo {cargoCode}" if cargoCode else ""
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidato número '{candidateNumber}'{cargoMsg} não foi localizado."
            )

        return await self.getCandidateVotesBySq(connection, candidate["sq_candidato"])

    async def listAvailableCargos(self, connection: asyncpg.Connection) -> List[Dict[str, Any]]:
        """Lista cargos eleitorais com cache de longa duração."""
        cacheKey = "electoral:cargos:list"
        cached = await CacheService.get(cacheKey)
        if cached:
            return cached

        cargos = await self.candidate_repo.listCargos(connection)
        ttl = await SystemConfigService.getInt(connection, "cache_ttl.cargos", 86400 * 30)
        await CacheService.set(cacheKey, cargos, ttlSeconds=ttl)
        return cargos

    async def listAvailableEleicoes(self, connection: asyncpg.Connection) -> List[Dict[str, Any]]:
        """Lista os pleitos com dados carregados (curto TTL — muda quando um novo
        pleito é ingerido, ao contrário dos cargos que são praticamente estáticos)."""
        cacheKey = "electoral:eleicoes:list"
        cached = await CacheService.get(cacheKey)
        if cached:
            return cached

        eleicoes = await self.candidate_repo.listEleicoes(connection)
        ttl = await SystemConfigService.getInt(connection, "cache_ttl.eleicoes", 3600)
        await CacheService.set(cacheKey, eleicoes, ttlSeconds=ttl)
        return eleicoes
