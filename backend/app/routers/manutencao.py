from typing import List

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import getDbConnection, require_role
from app.core.rate_limit import RateLimiter
from app.repositories.manutencao_repository import ManutencaoRepository
from app.schemas.manutencao import AtivarPleitoRequest, CargaEtl, JobEtl, JobEtlCreate, PleitoAtivo, SaudePleito
from app.services.system_config_service import SystemConfigService
from app.core.redis_client import CacheService
from app.schemas.user import UserInDB

router = APIRouter(
    prefix="/api/v1/admin/manutencao",
    tags=["Manutenção de Dados Eleitorais"],
    dependencies=[Depends(RateLimiter(times=10, seconds=1))]
)


@router.get(
    "/saude",
    response_model=List[SaudePleito],
    summary="Saúde dos dados por pleito carregado (votação e comparecimento)"
)
async def saude_por_pleito(
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> List[SaudePleito]:
    """Dados globais da instância. Requer papel admin."""
    registros = await ManutencaoRepository.saudePorPleito(connection)
    return [SaudePleito(**registro) for registro in registros]


@router.get(
    "/cargas",
    response_model=List[CargaEtl],
    summary="Histórico de cargas do ETL eleitoral, mais recente primeiro"
)
async def listar_cargas(
    limite: int = Query(50, ge=1, le=500),
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> List[CargaEtl]:
    """Requer papel admin."""
    registros = await ManutencaoRepository.listarCargas(connection, limite)
    return [CargaEtl(**registro) for registro in registros]


@router.get(
    "/jobs",
    response_model=List[JobEtl],
    summary="Fila de cargas do ETL (pendentes, em execução e concluídas)"
)
async def listar_jobs(
    limite: int = Query(20, ge=1, le=200),
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> List[JobEtl]:
    registros = await ManutencaoRepository.listarJobs(connection, limite)
    return [JobEtl(**registro) for registro in registros]


@router.post(
    "/jobs",
    response_model=JobEtl,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enfileira a carga de um pleito para o worker de ETL"
)
async def enfileirar_carga(
    payload: JobEtlCreate,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> JobEtl:
    """Exige a confirmação exata 'CARREGAR <TIPO> <ANO>' (ex.: CARREGAR VOTACAO 2026).
    Só um job ativo por vez: com outro em andamento, responde 409."""
    esperado = f"CARREGAR {payload.tipo.upper()} {payload.ano}"
    if payload.confirmacao.strip() != esperado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Confirmação inválida. Digite exatamente: {esperado}",
        )
    try:
        registro = await ManutencaoRepository.criarJob(connection, payload.tipo, payload.ano, current_user.email)
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma carga pendente ou em execução. Aguarde ela terminar.",
        )
    return JobEtl(**registro)


@router.post(
    "/ativar-pleito",
    response_model=PleitoAtivo,
    summary="Torna um pleito carregado o ativo da plataforma, com checagem e auditoria"
)
async def ativar_pleito(
    payload: AtivarPleitoRequest,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> PleitoAtivo:
    """Gates, nesta ordem:
    1. o pleito existe em tb_eleicoes (404);
    2. existe carga de votação concluída com sucesso para ele (409);
    3. se houver códigos de município sem cadastro, exige aceitação explícita (409);
    4. a confirmação deve ser exatamente 'ATIVAR <ANO>' (400).
    Grava o novo pleito em tb_configuracoes_sistema e registra a troca em tb_auditoria_manutencao."""
    pleito = await ManutencaoRepository.pleito(connection, payload.cd_eleicao)
    if pleito is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pleito não encontrado.")
    ano = pleito["ano_eleicao"]

    if not await ManutencaoRepository.existeCargaOkDeVotacao(connection, payload.cd_eleicao, ano):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não há carga de votação concluída com sucesso para este pleito.",
        )

    saude = next((s for s in await ManutencaoRepository.saudePorPleito(connection)
                  if s["cd_eleicao"] == payload.cd_eleicao), None)
    semCadastro = saude["codigos_sem_cadastro"] if saude else 0
    if semCadastro > 0 and not payload.aceitar_codigos_sem_cadastro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{semCadastro} código(s) de município sem cadastro. Confirme que aceita ativar mesmo assim.",
        )

    esperado = f"ATIVAR {ano}"
    if payload.confirmacao.strip() != esperado:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Confirmação inválida. Digite exatamente: {esperado}")

    anteriorAno = await SystemConfigService.getInt(connection, "eleitoral.election_year", 0)
    anteriorCd = await SystemConfigService.getStr(connection, "eleitoral.tse_codigo_eleicao", "")

    # Troca e auditoria na mesma transação: se a auditoria falhar, a troca é desfeita.
    async with connection.transaction():
        await SystemConfigService.updateMany(connection, {
            "eleitoral.election_year": str(ano),
            "eleitoral.tse_codigo_eleicao": payload.cd_eleicao,
        })
        await ManutencaoRepository.registrarAuditoria(
            connection, "ativar_pleito",
            {
                "anterior": {"ano": anteriorAno, "cd_eleicao": anteriorCd},
                "novo": {"ano": ano, "cd_eleicao": payload.cd_eleicao},
                "codigos_sem_cadastro": semCadastro,
                "aceitou_codigos_sem_cadastro": payload.aceitar_codigos_sem_cadastro,
            },
            current_user.email,
        )
    # Listas eleitorais têm TTL longo: sem invalidar, o seletor continuaria mostrando o pleito antigo.
    await CacheService.delete("electoral:eleicoes:list")
    await CacheService.delete("electoral:cargos:list")
    return PleitoAtivo(cd_eleicao=payload.cd_eleicao, ano_eleicao=ano,
                       anterior_cd_eleicao=anteriorCd, anterior_ano_eleicao=anteriorAno)
