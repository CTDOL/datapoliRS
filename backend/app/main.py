import os
import logging
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

from app.core.config import settings
from app.core.database import initializeDatabasePool, closeDatabasePool, getDatabaseConnection
from app.core.redis_client import initializeRedisClient, closeRedisClient
from app.core.dependencies import getDbConnection
from app.core.bootstrap import ensureAdminUser
from app.schemas.candidate import CandidataDetalhada
from app.services.tse_service import TSEService
from app.services.voting_service import VotingService
from app.services.system_config_service import SystemConfigService
from app.routers.geo import router as geo_router
from app.routers.voting import router as voting_router
from app.routers.cabinet import router as cabinet_router
from app.routers.amendments import router as amendments_router
from app.routers.legislative import router as legislative_router
from app.routers.tasks import router as tasks_router
from app.routers.auth import router as auth_router
from app.routers.tenant import router as tenant_router
from app.routers.admin import router as admin_router

# Configuração de Logging Estruturado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DataPoliRS_API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (Startup e Shutdown de Conexões)."""
    logger.info("=== INICIALIZANDO ECOSSISTEMA DATAPOLIRS ===")
    await initializeDatabasePool()
    await initializeRedisClient()
    await ensureAdminUser()
    async for connection in getDatabaseConnection():
        await SystemConfigService.warmCache(connection)
        break
    logger.info("=== DATAPOLIRS PRONTO PARA RECEBER REQUISIÇÕES ===")
    yield
    logger.info("=== ENCERRANDO RECURSOS DO DATAPOLIRS ===")
    await closeDatabasePool()
    await closeRedisClient()
    logger.info("=== SERVIÇOS FINALIZADOS COM SUCESSO ===")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

from app.core.exceptions import register_exception_handlers

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra Global Exception Handlers (RFC 7807)
register_exception_handlers(app)

# Monta o diretório de arquivos estáticos (Frontend)
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Fotos de liderança enviadas via upload — volume dedicado e persistente
# (datapolirs_uploads_data), separado de app/static que é conteúdo do build.
os.makedirs("app/uploads/liderancas", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

# Registro dos Controladores da Sprint 2
app.include_router(geo_router)
app.include_router(voting_router)
app.include_router(cabinet_router)
app.include_router(amendments_router)
app.include_router(legislative_router)
app.include_router(tasks_router)
app.include_router(auth_router)
app.include_router(tenant_router)
app.include_router(admin_router)

tse_service = TSEService(timeout=settings.TSE_TIMEOUT_SECONDS)


@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serve a interface web SPA do datapoliRS."""
    return FileResponse("app/static/index.html")


@app.get("/health", tags=["Monitoramento"])
async def health_check():
    """Healthcheck para probes do Docker."""
    return {
        "status": "online",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get(
    "/api/v1/candidatas/rs",
    response_model=CandidataDetalhada,
    tags=["Compatibilidade Legada TSE"]
)
async def consultar_deputada_rs(
    nome: str = Query(..., description="Nome civil ou de urna"),
    ano: Optional[int] = Query(None, description="Ano eleitoral (padrão: configuração da plataforma)"),
    codigo_eleicao: Optional[str] = Query(None, description="Código do pleito no TSE (padrão: configuração da plataforma)"),
    cd_cargo: Optional[int] = Query(None, description="Código do cargo — 7=Dep. Estadual, 6=Dep. Federal, 5=Senador, 3=Governador (padrão: configuração da plataforma)"),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    """Consulta direta ao DivulgaCandContas do TSE (mantida para compatibilidade)."""
    ano = ano if ano is not None else await SystemConfigService.getInt(connection, "eleitoral.election_year", settings.ELECTION_YEAR)
    codigo_eleicao = codigo_eleicao or await SystemConfigService.getStr(connection, "eleitoral.tse_codigo_eleicao", settings.TSE_CODIGO_ELEICAO)
    cd_cargo = cd_cargo if cd_cargo is not None else await SystemConfigService.getInt(connection, "eleitoral.default_cargo_code", settings.DEFAULT_CARGO_CODE)
    resultado = await tse_service.pesquisar_deputada_rs(nome, ano, codigo_eleicao, cd_cargo)
    if not resultado:
        raise HTTPException(
            status_code=404,
            detail=f"Candidatura '{nome}' não localizada no TSE para o pleito {ano} no RS."
        )
    return resultado


@app.get(
    "/api/v1/candidatas/{numero}/votos",
    tags=["Compatibilidade Legada TSE"]
)
async def obter_votos_candidata_legado(
    numero: int,
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    """Endpoint legado agora redirecionado para o PostgreSQL com alta performance."""
    votacao = await VotingService.getCandidateVotesByNumber(connection, candidateNumber=numero)
    return [{"municipio": item.nm_municipio, "votos": item.votos} for item in votacao.distribuicao_municipios]


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run("app.main:app", host="0.0.0.0", port=porta, reload=(settings.ENVIRONMENT == "development"))
