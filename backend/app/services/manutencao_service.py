from typing import List

import asyncpg
from fastapi import HTTPException, status

from app.core.redis_client import CacheService
from app.repositories.manutencao_repository import ManutencaoRepository
from app.schemas.manutencao import AtivarPleitoRequest, CargaEtl, JobEtl, JobEtlCreate, PleitoAtivo, SaudePleito
from app.services.system_config_service import SystemConfigService


class ManutencaoService:
    """Regras da área de Manutenção de Dados Eleitorais (ADR 033), restrita ao super-admin."""

    def __init__(self, manutencao_repo: ManutencaoRepository):
        self.manutencao_repo = manutencao_repo

    async def saude_por_pleito(self, connection: asyncpg.Connection) -> List[SaudePleito]:
        registros = await self.manutencao_repo.saudePorPleito(connection)
        return [SaudePleito(**registro) for registro in registros]

    async def listar_cargas(self, connection: asyncpg.Connection, limite: int) -> List[CargaEtl]:
        registros = await self.manutencao_repo.listarCargas(connection, limite)
        return [CargaEtl(**registro) for registro in registros]

    async def listar_jobs(self, connection: asyncpg.Connection, limite: int) -> List[JobEtl]:
        registros = await self.manutencao_repo.listarJobs(connection, limite)
        return [JobEtl(**registro) for registro in registros]

    async def enfileirar_carga(self, connection: asyncpg.Connection, payload: JobEtlCreate, operador: str) -> JobEtl:
        """Exige a confirmação exata 'CARREGAR <TIPO> <ANO>'. Com outro job ativo, responde 409."""
        esperado = f"CARREGAR {payload.tipo.upper()} {payload.ano}"
        if payload.confirmacao.strip() != esperado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Confirmação inválida. Digite exatamente: {esperado}",
            )
        try:
            registro = await self.manutencao_repo.criarJob(connection, payload.tipo, payload.ano, operador)
        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma carga pendente ou em execução. Aguarde ela terminar.",
            )
        return JobEtl(**registro)

    async def ativar_pleito(self, connection: asyncpg.Connection, payload: AtivarPleitoRequest, operador: str) -> PleitoAtivo:
        """Gates, nesta ordem:
        1. o pleito existe em tb_eleicoes (404);
        2. existe carga de votação concluída com sucesso para ele (409);
        3. se houver códigos de município sem cadastro, exige aceitação explícita (409);
        4. a confirmação deve ser exatamente 'ATIVAR <ANO>' (400).
        Grava o novo pleito em tb_configuracoes_sistema e registra a troca em tb_auditoria_manutencao."""
        pleito = await self.manutencao_repo.pleito(connection, payload.cd_eleicao)
        if pleito is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pleito não encontrado.")
        ano = pleito["ano_eleicao"]

        if not await self.manutencao_repo.existeCargaOkDeVotacao(connection, payload.cd_eleicao, ano):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não há carga de votação concluída com sucesso para este pleito.",
            )

        saude = next((s for s in await self.manutencao_repo.saudePorPleito(connection)
                      if s["cd_eleicao"] == payload.cd_eleicao), None)
        sem_cadastro = saude["codigos_sem_cadastro"] if saude else 0
        if sem_cadastro > 0 and not payload.aceitar_codigos_sem_cadastro:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{sem_cadastro} código(s) de município sem cadastro. Confirme que aceita ativar mesmo assim.",
            )

        esperado = f"ATIVAR {ano}"
        if payload.confirmacao.strip() != esperado:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Confirmação inválida. Digite exatamente: {esperado}")

        ano_anterior = await SystemConfigService.getInt(connection, "eleitoral.election_year", 0)
        cd_anterior = await SystemConfigService.getStr(connection, "eleitoral.tse_codigo_eleicao", "")

        # Troca e auditoria na mesma transação: se a auditoria falhar, a troca é desfeita.
        async with connection.transaction():
            await SystemConfigService.updateMany(connection, {
                "eleitoral.election_year": str(ano),
                "eleitoral.tse_codigo_eleicao": payload.cd_eleicao,
            })
            await self.manutencao_repo.registrarAuditoria(
                connection, "ativar_pleito",
                {
                    "anterior": {"ano": ano_anterior, "cd_eleicao": cd_anterior},
                    "novo": {"ano": ano, "cd_eleicao": payload.cd_eleicao},
                    "codigos_sem_cadastro": sem_cadastro,
                    "aceitou_codigos_sem_cadastro": payload.aceitar_codigos_sem_cadastro,
                },
                operador,
            )
        # Listas eleitorais têm TTL longo: sem invalidar, o seletor continuaria mostrando o pleito antigo.
        await CacheService.delete("electoral:eleicoes:list")
        await CacheService.delete("electoral:cargos:list")
        return PleitoAtivo(cd_eleicao=payload.cd_eleicao, ano_eleicao=ano,
                           anterior_cd_eleicao=cd_anterior, anterior_ano_eleicao=ano_anterior)
