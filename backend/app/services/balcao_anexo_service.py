import hashlib
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import asyncpg
from fastapi import HTTPException, status
from app.core.exceptions import DomainException
from app.repositories.balcao_repository import BalcaoRepository
from app.services.image_sanitizer_service import ImageSanitizerService

logger = logging.getLogger("BalcaoAnexoService")

LIMITE_BYTES = 10 * 1024 * 1024
ASSINATURA_PDF = b"%PDF-"
MIME_POR_EXTENSAO = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp", "pdf": "application/pdf"}


@dataclass(frozen=True)
class AnexoClassificado:
    conteudo: bytes
    extensao: str
    mime_type: str
    sha256: str


def _pastaBase() -> str:
    # Mesma variável de cabinet.py (cujo padrão é a pasta das fotos); os anexos ficam em UPLOADS_DIR/balcao.
    return os.environ.get("UPLOADS_DIR", "app/uploads/liderancas")


class BalcaoAnexoService:
    LIMITE_BYTES = LIMITE_BYTES

    @staticmethod
    def classificar(conteudo: bytes) -> AnexoClassificado:
        """O tipo vale pelo conteúdo, nunca pela extensão nem pelo content-type declarado.

        PDF: assinatura %PDF- e até 10 MB. Imagem: ImageSanitizerService (JPEG, PNG, WEBP), que descarta
        EXIF. Qualquer outro tipo: 415; acima de 10 MB: 413.
        """
        if len(conteudo) > LIMITE_BYTES:
            raise DomainException("Arquivo acima do limite de 10 MB.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                  "Payload Too Large")
        if not conteudo:
            raise DomainException("Arquivo vazio.", status.HTTP_422_UNPROCESSABLE_ENTITY, "Arquivo inválido")
        if conteudo.startswith(ASSINATURA_PDF):
            return AnexoClassificado(conteudo, "pdf", MIME_POR_EXTENSAO["pdf"], hashlib.sha256(conteudo).hexdigest())
        try:
            imagem = ImageSanitizerService.sanitize(conteudo)
        except HTTPException as erro:
            raise DomainException(str(erro.detail), erro.status_code,
                                  "Tipo de arquivo não suportado" if erro.status_code == 415 else "Arquivo inválido")
        return AnexoClassificado(imagem.conteudo, imagem.extensao, MIME_POR_EXTENSAO[imagem.extensao], imagem.sha256)

    @staticmethod
    def _gravarEmDisco(tenantId: uuid.UUID, anexo: AnexoClassificado) -> Tuple[str, str]:
        relativo = f"balcao/{tenantId}/{uuid.uuid4().hex}.{anexo.extensao}"
        absoluto = os.path.join(_pastaBase(), relativo)
        os.makedirs(os.path.dirname(absoluto), exist_ok=True)
        with open(absoluto, "wb") as destino:
            destino.write(anexo.conteudo)
        return relativo, absoluto

    @staticmethod
    async def salvar(connection: asyncpg.Connection, tenantId: uuid.UUID, anexo: AnexoClassificado,
                     entradaId: Optional[uuid.UUID] = None,
                     atendimentoId: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Grava o arquivo com nome do servidor e o registro no banco (caminho relativo, hash, tipo, tamanho).
        Se o banco falhar, o arquivo é apagado."""
        relativo, absoluto = BalcaoAnexoService._gravarEmDisco(tenantId, anexo)
        try:
            return await BalcaoRepository.criarAnexo(
                connection, tenantId, entradaId, atendimentoId, relativo, anexo.sha256,
                anexo.mime_type, len(anexo.conteudo),
            )
        except Exception:
            try:
                os.remove(absoluto)
            except OSError:
                logger.warning("Não foi possível apagar o anexo órfão.")
            raise

    @staticmethod
    async def obterParaDownload(connection: asyncpg.Connection, tenantId: uuid.UUID,
                                anexoId: uuid.UUID) -> Tuple[str, str, str]:
        """Devolve (caminho absoluto, mime, nome para download). Outro gabinete recebe 404."""
        registro = await BalcaoRepository.obterAnexo(connection, tenantId, anexoId)
        naoEncontrado = DomainException("Anexo não encontrado.", status.HTTP_404_NOT_FOUND, "Não encontrado")
        if registro is None:
            raise naoEncontrado
        base = os.path.realpath(_pastaBase())
        absoluto = os.path.realpath(os.path.join(base, registro["caminho_arquivo"]))
        if not absoluto.startswith(base + os.sep) or not os.path.isfile(absoluto):
            raise naoEncontrado
        extensao = absoluto.rsplit(".", 1)[-1]
        return absoluto, registro["mime_type"], f"anexo-{registro['id']}.{extensao}"
