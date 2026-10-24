import os
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
import asyncpg
from app.core.dependencies import getDbConnection, bloquear_super_admin
from app.core.rate_limit import RateLimiter
from app.repositories.cabinet_repository import CabinetRepository
from app.routers.cabinet import UPLOADS_DIR
from app.schemas.user import UserInDB

# Nomes gravados pelo upload: `{id_lideranca}-{hash}.{ext}` e o antigo `{id_lideranca}.{ext}`.
# Qualquer outro nome é recusado antes de tocar no disco (sem caminho relativo possível).
NOME_DA_FOTO = re.compile(
    r"^(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:-[0-9a-f]{16})?\.(?:jpg|jpeg|png|webp)$"
)

router = APIRouter(
    prefix="/uploads/liderancas",
    tags=["Fotos de Lideranças"],
    # O mapa carrega uma foto por liderança de uma vez: limite mais largo que o das rotas de dados.
    dependencies=[Depends(RateLimiter(times=100, seconds=1, configKey="fotos"))]
)

FOTO_NAO_ENCONTRADA = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto não encontrada.")


@router.get("/{arquivo}", summary="Foto de liderança, só para o gabinete dono (revisão de 2026-10-24, M2)")
async def obter_foto_lideranca(
    arquivo: str,
    current_user: UserInDB = Depends(bloquear_super_admin),
    connection: asyncpg.Connection = Depends(getDbConnection)
) -> FileResponse:
    nome = NOME_DA_FOTO.match(arquivo)
    if not nome:
        raise FOTO_NAO_ENCONTRADA
    # Outro gabinete recebe 404, como nas demais rotas: não revela que a liderança existe.
    if not await CabinetRepository.pertenceAoGabinete(connection, current_user.tenant_id, uuid.UUID(nome["id"])):
        raise FOTO_NAO_ENCONTRADA
    caminho = os.path.join(UPLOADS_DIR, arquivo)
    if not os.path.isfile(caminho):
        raise FOTO_NAO_ENCONTRADA
    # Cache só no navegador do usuário: a resposta depende da sessão.
    return FileResponse(caminho, headers={"Cache-Control": "private, max-age=3600"})
