from typing import List, Optional, Dict, Any
import httpx
from fastapi import APIRouter, Depends, Query, Response
import asyncpg
from app.core.dependencies import getDbConnection
from app.services.voting_service import VotingService
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.voting_repository import VotingRepository
from app.schemas.voting import CandidatoBuscaItem, VotacaoCandidatoResponse
from app.core.rate_limit import RateLimiter

def get_voting_service() -> VotingService:
    return VotingService(
        candidate_repo=CandidateRepository(),
        voting_repo=VotingRepository()
    )

router = APIRouter(
    prefix="/api/v1", 
    tags=["Inteligência Eleitoral & Votação"],
    dependencies=[Depends(RateLimiter(times=20, seconds=1))]
)


@router.get(
    "/candidatos/{sq_candidato}/foto",
    summary="Recupera a foto oficial do candidato via TSE com fallback",
    response_class=Response
)
async def obter_foto_candidato(sq_candidato: int):
    """Proxy resiliente para fotos oficiais do TSE."""
    tse_photo_url = f"https://divulgacandcontas.tse.jus.br/divulga/rest/arquivo/img/2040602022/{sq_candidato}/RS"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                tse_photo_url,
                headers={"User-Agent": "Mozilla/5.0 (datapoliRS API)"}
            )
            if resp.status_code == 200 and resp.content:
                contentType = resp.headers.get("content-type", "image/jpeg")
                return Response(
                    content=resp.content,
                    media_type=contentType,
                    headers={"Cache-Control": "public, max-age=604800"}
                )
    except Exception:
        pass

    # Fallback SVG Avatar
    svgAvatar = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
        <circle cx="60" cy="60" r="60" fill="#e2e8f0"/>
        <circle cx="60" cy="46" r="22" fill="#94a3b8"/>
        <path d="M22 108 c0 -24 18 -38 38 -38 s38 14 38 38 Z" fill="#94a3b8"/>
    </svg>"""
    return Response(content=svgAvatar, media_type="image/svg+xml")


@router.get(
    "/cargos",
    response_model=List[Dict[str, Any]],
    summary="Lista cargos eletivos disponíveis"
)
async def listar_cargos(
    connection: asyncpg.Connection = Depends(getDbConnection),
    voting_service: VotingService = Depends(get_voting_service)
) -> List[Dict[str, Any]]:
    """Retorna os cargos mapeados no pleito (Deputado Estadual, Federal, Senador, Governador)."""
    return await voting_service.listAvailableCargos(connection)


@router.get(
    "/candidatos",
    response_model=List[CandidatoBuscaItem],
    summary="Pesquisa candidatos multi-cargo com filtros"
)
async def pesquisar_candidatos(
    termo: Optional[str] = Query(None, description="Nome civil ou nome de urna do candidato"),
    cargo: Optional[int] = Query(None, alias="cd_cargo", description="Código do cargo (ex: 7=Deputado Estadual, 6=Deputado Federal)"),
    partido: Optional[str] = Query(None, alias="sg_partido", description="Sigla do partido (ex: PT, PP, PL, MDB)"),
    numero: Optional[int] = Query(None, alias="nr_candidato", description="Número eleitoral na urna"),
    ano: int = Query(2022, description="Ano da eleição"),
    limite: int = Query(50, ge=1, le=200, description="Quantidade máxima de resultados"),
    connection: asyncpg.Connection = Depends(getDbConnection),
    voting_service: VotingService = Depends(get_voting_service)
) -> List[CandidatoBuscaItem]:
    """Busca avançada de candidaturas no banco relacional."""
    return await voting_service.searchCandidates(
        connection=connection,
        searchTerm=termo,
        cargoCode=cargo,
        partidoSigla=partido,
        candidateNumber=numero,
        ano=ano,
        limit=limite
    )


@router.get(
    "/votacao/candidatos/{sq_candidato}/municipios",
    response_model=VotacaoCandidatoResponse,
    summary="Mapa analítico de votação por município (SQ do Candidato)"
)
async def obter_votacao_candidato_por_sq(
    sq_candidato: int,
    connection: asyncpg.Connection = Depends(getDbConnection),
    voting_service: VotingService = Depends(get_voting_service)
) -> VotacaoCandidatoResponse:
    """Retorna a soma de votos nominais por município e percentual de dominância eleitoral."""
    return await voting_service.getCandidateVotesBySq(connection, sq_candidato)


@router.get(
    "/votacao/numero/{numero_urna}",
    response_model=VotacaoCandidatoResponse,
    summary="Mapa analítico de votação por número de urna"
)
async def obter_votacao_candidato_por_numero(
    numero_urna: int,
    cargo: Optional[int] = Query(None, alias="cd_cargo", description="Filtrar por cargo específico"),
    ano: int = Query(2022, description="Ano da eleição"),
    connection: asyncpg.Connection = Depends(getDbConnection),
    voting_service: VotingService = Depends(get_voting_service)
) -> VotacaoCandidatoResponse:
    """Busca o candidato pelo número eleitoral e retorna sua distribuição de votos no RS."""
    return await voting_service.getCandidateVotesByNumber(
        connection=connection,
        candidateNumber=numero_urna,
        cargoCode=cargo,
        ano=ano
    )
