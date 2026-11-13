from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
import asyncpg
from app.core.dependencies import getDbConnection
from app.core.rate_limit import RateLimiter
from app.schemas.balcao import PortalEntradaResposta
from app.services.balcao_anexo_service import BalcaoAnexoService
from app.services.balcao_portal_service import BalcaoPortalService

# Rota pública: sem login. O limite é por IP, 5 por minuto, e o portal recusa com 503 se o Redis cair
# (falha fechada), porque grava dado de quem não tem conta.
router = APIRouter(
    prefix="/api/v1/portal",
    tags=["Balcão — Portal público"],
    dependencies=[Depends(RateLimiter(times=5, seconds=60, configKey="balcao_portal", falhaFechada=True))]
)


@router.post(
    "/{token}/entradas",
    response_model=PortalEntradaResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Envio de uma demanda pelo cidadão, com o token do portal do gabinete"
)
async def receber_entrada(
    token: str,
    texto: Optional[str] = Form(None),
    anexo: Optional[UploadFile] = File(None),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> PortalEntradaResposta:
    conteudo = None
    if anexo is not None and anexo.filename:
        # Lê um byte além do teto para o service distinguir "exatamente 10 MB" de "acima de 10 MB".
        conteudo = await anexo.read(BalcaoAnexoService.LIMITE_BYTES + 1)
    mensagem = await BalcaoPortalService.receberEntrada(connection, token, texto, conteudo)
    return PortalEntradaResposta(mensagem=mensagem)
