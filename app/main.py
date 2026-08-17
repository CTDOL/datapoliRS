import os
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.schemas.candidate import CandidataDetalhada
from app.services.tse_service import TSEService

app = FastAPI(
    title="API de Consulta Eleitoral - Deputadas Estaduais RS",
    version="1.0.0",
    description="Microsserviço de busca e normalização de dados eleitorais via DivulgaCandContas (TSE)."
)

# Monta a pasta de arquivos estáticos
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

tse_service = TSEService()

@app.get("/", tags=["Frontend"])
async def serve_frontend():
    return FileResponse("app/static/index.html")


@app.get("/health", tags=["Monitoramento"])
async def health_check():
    return {"status": "online"}


@app.get(
    "/api/v1/candidatas/rs",
    response_model=CandidataDetalhada,
    tags=["Candidaturas RS"]
)
async def consultar_deputada_rs(
    nome: str = Query(..., description="Nome civil ou nome de urna da candidata"),
    ano: int = Query(2022, description="Ano do pleito eleitoral"),
    codigo_eleicao: str = Query("2040602022", description="Código do pleito no TSE")
):
    resultado = await tse_service.pesquisar_deputada_rs(nome, ano, codigo_eleicao)
    if not resultado:
        raise HTTPException(
            status_code=404,
            detail=f"Deputada '{nome}' não localizada para o pleito {ano} no RS."
        )
    return resultado


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=porta, reload=False)
