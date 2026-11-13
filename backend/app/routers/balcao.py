import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse
import asyncpg
from app.core.dependencies import bloquear_super_admin, get_current_user, getDbConnection, require_role
from app.core.rate_limit import RateLimiter
from app.schemas.balcao import (
    AnexoCriadoResposta, DescartarRequest, DescartarResponse, EfetivarRequest, EfetivarResponse,
    EntradaDetalhe, EntradaResumo, EventoTimeline, GrafoResposta, PortalCriadoResposta,
    PortalRevogadoResposta, ResolverRequest, ResolverResponse,
)
from app.schemas.user import UserInDB
from app.services.balcao_anexo_service import BalcaoAnexoService
from app.services.balcao_caixa_service import BalcaoCaixaService
from app.services.balcao_grafo_service import BalcaoGrafoService
from app.services.balcao_portal_service import BalcaoPortalService
from app.services.balcao_resolucao_service import BalcaoResolucaoService

# Rotas internas do Balcão: sessão obrigatória, conta da plataforma bloqueada (ADR 039) e gabinete
# sempre o de current_user.tenant_id, como em tasks.py. O router só chama service.
router = APIRouter(
    prefix="/api/v1/balcao",
    tags=["Balcão Inteligente"],
    dependencies=[Depends(RateLimiter(times=30, seconds=1, configKey="balcao")), Depends(bloquear_super_admin)]
)

PAPEIS_DE_ESCRITA = ["admin", "operador"]


@router.get("/entradas", response_model=List[EntradaResumo], summary="Caixa de entrada (filtro opcional por status)")
async def listar_entradas(
    status_: Optional[str] = Query(None, alias="status"),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoCaixaService.listarEntradas(connection, current_user.tenant_id, status_)


@router.get("/entradas/{id_entrada}", response_model=EntradaDetalhe, summary="Entrada com sugestões e anexos")
async def obter_entrada(
    id_entrada: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoCaixaService.obterEntrada(connection, current_user.tenant_id, id_entrada)


@router.post("/entradas/{id_entrada}/efetivar", response_model=EfetivarResponse,
             status_code=status.HTTP_201_CREATED, summary="Efetiva a entrada: atendido, protocolo e timeline")
async def efetivar_entrada(
    id_entrada: uuid.UUID,
    payload: EfetivarRequest,
    current_user: UserInDB = Depends(require_role(PAPEIS_DE_ESCRITA)),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoCaixaService.efetivar(connection, current_user, id_entrada, payload)


@router.post("/entradas/{id_entrada}/descartar", response_model=DescartarResponse, summary="Descarta a entrada")
async def descartar_entrada(
    id_entrada: uuid.UUID,
    payload: DescartarRequest,
    current_user: UserInDB = Depends(require_role(PAPEIS_DE_ESCRITA)),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoCaixaService.descartar(connection, current_user, id_entrada, payload)


@router.get("/atendidos/{id_atendido}/timeline", response_model=List[EventoTimeline],
            summary="Linha do tempo do atendido (somente leitura)")
async def timeline_do_atendido(
    id_atendido: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoCaixaService.timeline(connection, current_user.tenant_id, id_atendido)


@router.get("/anexos/{id_anexo}", summary="Baixa o anexo (sempre como download, nunca inline)")
async def baixar_anexo(
    id_anexo: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> FileResponse:
    caminho, mime, nomeParaDownload = await BalcaoCaixaService.anexoParaDownload(
        connection, current_user.tenant_id, id_anexo
    )
    return FileResponse(
        caminho, media_type=mime, filename=nomeParaDownload, content_disposition_type="attachment",
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"},
    )


@router.post("/portais", response_model=PortalCriadoResposta, status_code=status.HTTP_201_CREATED,
             summary="Cria um portal; o token em claro só aparece nesta resposta")
async def criar_portal(
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoPortalService.criarPortal(connection, current_user.tenant_id)


@router.post("/portais/{id_portal}/revogar", response_model=PortalRevogadoResposta, summary="Revoga um portal")
async def revogar_portal(
    id_portal: uuid.UUID,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoPortalService.revogarPortal(connection, current_user.tenant_id, id_portal)


@router.post("/atendimentos/{id_atendimento}/anexos", response_model=AnexoCriadoResposta,
             status_code=status.HTTP_201_CREATED, summary="Anexa um arquivo (imagem ou PDF) ao atendimento")
async def anexar_ao_atendimento(
    id_atendimento: uuid.UUID,
    anexo: UploadFile = File(...),
    current_user: UserInDB = Depends(require_role(PAPEIS_DE_ESCRITA)),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    conteudo = await anexo.read(BalcaoAnexoService.LIMITE_BYTES + 1)
    return await BalcaoCaixaService.anexarAoAtendimento(connection, current_user.tenant_id, id_atendimento, conteudo)


@router.post("/atendimentos/{id_atendimento}/resolver", response_model=ResolverResponse,
             status_code=status.HTTP_201_CREATED, summary="Resolve o atendimento com despacho e evidência")
async def resolver_atendimento(
    id_atendimento: uuid.UUID,
    payload: ResolverRequest,
    current_user: UserInDB = Depends(require_role(PAPEIS_DE_ESCRITA)),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoResolucaoService.resolver(connection, current_user, id_atendimento, payload)


@router.get("/grafo", response_model=GrafoResposta, summary="Grafo de correlações do gabinete")
async def grafo(
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoGrafoService.montar(connection, current_user.tenant_id)
