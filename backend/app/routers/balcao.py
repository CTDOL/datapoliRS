import uuid
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, File, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
import asyncpg
from app.core.dependencies import bloquear_super_admin, get_current_user, getDbConnection, require_role
from app.core.rate_limit import RateLimiter
from app.schemas.balcao import (
    AnexoCriadoResposta, CategoriaResumo, DescartarRequest, DescartarResponse, EfetivarRequest, EfetivarResponse,
    EntradaDetalhe, EntradaResumo, EventoTimeline, GrafoResposta, IaConfigAtualizarRequest,
    IaConfigResposta, IaConfigTestarRequest, IaConfigTesteResposta, LiderancasSugeridasResposta,
    MotorAtivoResposta, PedidoMapaItem, PontoFocalAtualizarRequest, PontoFocalAtualizarResposta,
    PortalCriadoResposta, PortalCriarRequest, PortalResumo, PortalRevogadoResposta,
    ResolverRequest, ResolverResponse,
)
from app.schemas.user import UserInDB
from app.services import observabilidade_service
from app.services.balcao_anexo_service import BalcaoAnexoService
from app.services.balcao_caixa_service import BalcaoCaixaService
from app.services.balcao_grafo_service import BalcaoGrafoService
from app.services.balcao_ia_service import BalcaoIaService
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


@router.post("/entradas/{id_entrada}/analisar", response_model=EntradaDetalhe,
             dependencies=[Depends(RateLimiter(times=30, seconds=60))],
             summary="Reexecuta análise Regex e IA (se ativa) na entrada pendente")
async def analisar_entrada(
    id_entrada: uuid.UUID,
    current_user: UserInDB = Depends(require_role(PAPEIS_DE_ESCRITA)),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoCaixaService.analisarEntrada(connection, current_user.tenant_id, id_entrada)


@router.post("/entradas/{id_entrada}/efetivar", response_model=EfetivarResponse,
             status_code=status.HTTP_201_CREATED, summary="Efetiva a entrada: atendido, protocolo e timeline")
async def efetivar_entrada(
    id_entrada: uuid.UUID,
    payload: EfetivarRequest,
    request: Request,
    current_user: UserInDB = Depends(require_role(PAPEIS_DE_ESCRITA)),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    resultado = await BalcaoCaixaService.efetivar(connection, current_user, id_entrada, payload)
    await observabilidade_service.registrar_operacao(
        connection, "balcao_efetivado", request, current_user, status.HTTP_201_CREATED
    )
    return resultado


@router.post("/entradas/{id_entrada}/descartar", response_model=DescartarResponse, summary="Descarta a entrada")
async def descartar_entrada(
    id_entrada: uuid.UUID,
    payload: DescartarRequest,
    request: Request,
    current_user: UserInDB = Depends(require_role(PAPEIS_DE_ESCRITA)),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    resultado = await BalcaoCaixaService.descartar(connection, current_user, id_entrada, payload)
    await observabilidade_service.registrar_operacao(
        connection, "balcao_descartado", request, current_user, status.HTTP_200_OK
    )
    return resultado


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
    request: Request,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> FileResponse:
    caminho, mime, nomeParaDownload = await BalcaoCaixaService.anexoParaDownload(
        connection, current_user.tenant_id, id_anexo
    )
    await observabilidade_service.registrar_operacao(
        connection, "balcao_anexo_baixado", request, current_user, status.HTTP_200_OK
    )
    return FileResponse(
        caminho, media_type=mime, filename=nomeParaDownload, content_disposition_type="attachment",
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"},
    )


@router.get("/portais", response_model=List[PortalResumo], summary="Lista portais públicos do gabinete")
async def listar_portais(
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoPortalService.listarPortais(connection, current_user.tenant_id)


@router.post("/portais", response_model=PortalCriadoResposta, status_code=status.HTTP_201_CREATED,
             summary="Cria um portal público para o gabinete")
async def criar_portal(
    payload: Optional[PortalCriarRequest] = Body(default=None),
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    return await BalcaoPortalService.criarPortal(
        connection, current_user.tenant_id, payload.rotulo if payload else None
    )


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
    request: Request,
    current_user: UserInDB = Depends(require_role(PAPEIS_DE_ESCRITA)),
    connection: asyncpg.Connection = Depends(getDbConnection)
):
    resultado = await BalcaoResolucaoService.resolver(connection, current_user, id_atendimento, payload)
    await observabilidade_service.registrar_operacao(
        connection, "balcao_resolvido", request, current_user, status.HTTP_201_CREATED
    )
    return resultado


@router.get("/mapa-pedidos", response_model=List[PedidoMapaItem], summary="Pedidos registrados e em andamento para o mapa tático")
async def listar_pedidos_mapa(
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await BalcaoCaixaService.listarPedidosMapa(connection, current_user.tenant_id)


@router.patch("/atendimentos/{id_atendimento}/ponto-focal", response_model=PontoFocalAtualizarResposta,
               summary="Altera a liderança ponto-focal (1:1) do atendimento sem encerrá-lo")
async def atualizar_ponto_focal(
    id_atendimento: uuid.UUID,
    payload: PontoFocalAtualizarRequest,
    current_user: UserInDB = Depends(require_role(PAPEIS_DE_ESCRITA)),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await BalcaoCaixaService.atualizarPontoFocal(
        connection, current_user, id_atendimento, payload.lideranca_ponto_focal_id
    )


@router.get("/motor-ativo", response_model=MotorAtivoResposta,
            summary="Informa ao operador qual motor (Regex ou IA) está ativo no momento")
async def obter_motor_ativo(
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    config = await BalcaoIaService.obterConfiguracao(connection)
    return {"provider": config["provider"], "model": config["model"]}


@router.get("/liderancas-sugeridas", response_model=LiderancasSugeridasResposta,
            summary="Lista lideranças do gabinete priorizando as vinculadas ao município")
async def listar_liderancas_sugeridas(
    municipio_id: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await BalcaoCaixaService.listarLiderancasSugeridas(
        connection, current_user.tenant_id, municipio_id
    )


@router.get("/categorias", response_model=List[CategoriaResumo],
            summary="Lista categorias orgânicas de atendimento do gabinete")
async def listar_categorias(
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await BalcaoCaixaService.listarCategorias(connection, current_user.tenant_id)


@router.get("/grafo", response_model=GrafoResposta, summary="Grafo de correlações do gabinete")
async def grafo(
    incluir_resolvidos: bool = Query(False),
    municipio_id: Optional[str] = Query(None),
    categoria_id: Optional[uuid.UUID] = Query(None),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await BalcaoGrafoService.montar(
        connection,
        current_user.tenant_id,
        incluirResolvidos=incluir_resolvidos,
        municipioId=municipio_id.strip() if municipio_id else None,
        categoriaId=categoria_id,
    )


@router.get("/ia-config", response_model=IaConfigResposta, summary="Consulta o motor IA/Regex do Balcão")
async def obter_ia_config(
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await BalcaoIaService.obterConfiguracao(connection)


@router.put("/ia-config", response_model=IaConfigResposta, summary="Comuta o motor IA/Regex do Balcão em runtime")
async def atualizar_ia_config(
    payload: IaConfigAtualizarRequest,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await BalcaoIaService.atualizarConfiguracao(
        connection,
        payload.provider,
        payload.model,
        payload.base_url,
        apiKey=payload.api_key,
        limparApiKey=payload.limpar_api_key,
    )


@router.post("/ia-config/testar", response_model=IaConfigTesteResposta, summary="Testa conectividade do motor de IA do Balcão")
async def testar_ia_config(
    payload: IaConfigTestarRequest,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection),
):
    return await BalcaoIaService.testarConexao(
        connection,
        provider=payload.provider,
        model=payload.model,
        baseUrl=payload.base_url,
        apiKey=payload.api_key,
    )
