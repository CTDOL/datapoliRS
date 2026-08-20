import os
import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

from app.core.config import settings
from app.core.database import initializeDatabasePool, closeDatabasePool
from app.core.redis_client import initializeRedisClient, closeRedisClient
from app.core.dependencies import getDbConnection
from app.schemas.candidate import CandidataDetalhada
from app.services.tse_service import TSEService
from app.services.voting_service import VotingService
from app.routers.geo import router as geo_router
from app.routers.voting import router as voting_router
from app.routers.cabinet import router as cabinet_router
from app.routers.auth import router as auth_router

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

# Registro dos Controladores da Sprint 2
app.include_router(geo_router)
app.include_router(voting_router)
app.include_router(cabinet_router)
app.include_router(auth_router)

tse_service = TSEService(timeout=settings.TSE_TIMEOUT_SECONDS)


@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serve a interface web SPA do datapoliRS."""
    return FileResponse("app/static/index.html")


@app.get("/health", tags=["Monitoramento"])
async def health_check():
    """Healthcheck para probes do Docker e Render."""
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
    ano: int = Query(2022, description="Ano eleitoral"),
    codigo_eleicao: str = Query("2040602022", description="Código do pleito no TSE")
):
    """Consulta direta ao DivulgaCandContas do TSE (mantida para compatibilidade)."""
    resultado = await tse_service.pesquisar_deputada_rs(nome, ano, codigo_eleicao)
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
