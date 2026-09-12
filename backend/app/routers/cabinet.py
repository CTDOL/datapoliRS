import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, status
import asyncpg
from app.core.dependencies import getDbConnection, get_current_user, require_role
from app.schemas.user import UserInDB
from app.services.cabinet_service import CabinetService
from app.schemas.leadership import (
    LiderancaCreate,
    LiderancaUpdate,
    LiderancaResponse,
    LiderancaPageResponse
)
from app.core.rate_limit import RateLimiter

UPLOADS_DIR = "app/uploads/liderancas"
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FOTO_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

router = APIRouter(
    prefix="/api/v1/gabinete/liderancas",
    tags=["Gabinete Digital & Lideranças"],
    dependencies=[Depends(RateLimiter(times=30, seconds=1, configKey="cabinet"))]
)


@router.post(
    "",
    response_model=LiderancaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra uma nova liderança política no gabinete"
)
async def cadastrar_lideranca(
    payload: LiderancaCreate,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> LiderancaResponse:
    """Cria uma nova liderança vinculada exclusivamente ao gabinete (tenant_id)."""
    return await CabinetService.createLeadership(connection, current_user.tenant_id, payload)


@router.get(
    "",
    response_model=LiderancaPageResponse,
    summary="Lista as lideranças do gabinete, paginadas, com filtros"
)
async def listar_liderancas(
    cd_ibge_7: Optional[str] = Query(None, description="Filtrar por código IBGE do município"),
    tp_influencia: Optional[str] = Query(None, description="Filtrar por categoria de influência"),
    is_ativo: Optional[bool] = Query(None, description="Filtrar por status ativo/inativo"),
    termo: Optional[str] = Query(None, description="Busca por nome completo (case-insensitive, parcial)"),
    page: int = Query(1, ge=1, description="Número da página (1-indexado)"),
    page_size: int = Query(50, ge=1, le=200, description="Quantidade de registros por página"),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> LiderancaPageResponse:
    """Recupera a lista paginada de lideranças cadastradas no gabinete isolado."""
    return await CabinetService.listLeaderships(
        connection=connection,
        tenantId=current_user.tenant_id,
        ibgeCode=cd_ibge_7,
        influenceCategory=tp_influencia,
        isActive=is_ativo,
        searchTerm=termo,
        page=page,
        pageSize=page_size
    )


@router.get(
    "/{id_lideranca}",
    response_model=LiderancaResponse,
    summary="Recupera detalhes de uma liderança pelo ID"
)
async def obter_lideranca_por_id(
    id_lideranca: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> LiderancaResponse:
    """Retorna os dados cadastrais da liderança se pertencer ao gabinete autenticado."""
    return await CabinetService.getLeadershipById(connection, current_user.tenant_id, id_lideranca)


@router.put(
    "/{id_lideranca}",
    response_model=LiderancaResponse,
    summary="Atualiza dados de uma liderança"
)
async def atualizar_lideranca(
    id_lideranca: uuid.UUID,
    payload: LiderancaUpdate,
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> LiderancaResponse:
    """Atualiza as informações da liderança no gabinete."""
    return await CabinetService.updateLeadership(connection, current_user.tenant_id, id_lideranca, payload)


@router.post(
    "/{id_lideranca}/foto",
    response_model=LiderancaResponse,
    summary="Faz upload da foto de uma liderança (JPEG/PNG/WebP, até 5MB)"
)
async def enviar_foto_lideranca(
    id_lideranca: uuid.UUID,
    arquivo: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> LiderancaResponse:
    """Salva a foto em disco (volume dedicado) e associa a URL pública à liderança."""
    if arquivo.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato de imagem não suportado. Envie JPEG, PNG ou WebP."
        )

    conteudo = await arquivo.read()
    if len(conteudo) > MAX_FOTO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Imagem excede o limite de 5MB."
        )

    # Valida que a liderança existe e pertence a este tenant antes de tocar no disco.
    await CabinetService.getLeadershipById(connection, current_user.tenant_id, id_lideranca)

    extensao = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[arquivo.content_type]
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    caminhoArquivo = os.path.join(UPLOADS_DIR, f"{id_lideranca}.{extensao}")
    with open(caminhoArquivo, "wb") as destino:
        destino.write(conteudo)

    fotoUrl = f"/uploads/liderancas/{id_lideranca}.{extensao}"
    return await CabinetService.setFotoUrl(connection, current_user.tenant_id, id_lideranca, fotoUrl)


@router.delete(
    "/{id_lideranca}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma liderança do gabinete (requer papel admin)"
)
async def remover_lideranca(
    id_lideranca: uuid.UUID,
    current_user: UserInDB = Depends(require_role(["admin"])),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> None:
    """Exclui a liderança do gabinete garantindo isolamento por tenant_id (e a foto em disco, se houver)."""
    for extensao in ("jpg", "png", "webp"):
        caminhoArquivo = os.path.join(UPLOADS_DIR, f"{id_lideranca}.{extensao}")
        if os.path.exists(caminhoArquivo):
            os.remove(caminhoArquivo)
    await CabinetService.deleteLeadership(connection, current_user.tenant_id, id_lideranca)
