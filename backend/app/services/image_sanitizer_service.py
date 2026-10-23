import hashlib
import io
import logging
from dataclasses import dataclass
from fastapi import HTTPException, status
from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

# Formato real detectado pelo Pillow -> extensão gravada em disco.
# O content_type do multipart é declarado pelo cliente; este mapa vale pelo conteúdo.
FORMATOS_PERMITIDOS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}

# Teto de pixels decodificados. 5MB comprimidos podem virar gigabytes em memória
# (decompression bomb); 40 MP cobre com folga a câmera de qualquer celular.
MAX_PIXELS = 40_000_000

QUALIDADE_JPEG_WEBP = 90


@dataclass(frozen=True)
class ImagemSanitizada:
    conteudo: bytes
    extensao: str
    sha256: str


class ImageSanitizerService:
    """Sanitização de fotos de lideranças (FR-006): sem EXIF/GPS e com hash determinístico."""

    @staticmethod
    def sanitize(conteudo: bytes) -> ImagemSanitizada:
        """Decodifica a imagem, descarta todos os metadados e a regrava só com os pixels.

        A orientação do EXIF é aplicada aos pixels antes do descarte, para a foto
        de celular não aparecer deitada. O hash é calculado sobre os bytes já
        sanitizados, então o mesmo arquivo de entrada gera sempre o mesmo nome.
        """
        try:
            with Image.open(io.BytesIO(conteudo)) as imagem:
                formato = imagem.format
                if formato not in FORMATOS_PERMITIDOS:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="Formato de imagem não suportado. Envie JPEG, PNG ou WebP."
                    )
                if imagem.width * imagem.height > MAX_PIXELS:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Imagem com resolução acima do limite permitido."
                    )
                imagem.load()
                orientada = ImageOps.exif_transpose(imagem)
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as erro:
            logger.warning(f"Upload de foto rejeitado: conteúdo não é imagem válida ({erro}).")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Arquivo não é uma imagem válida. Envie JPEG, PNG ou WebP."
            )

        limpa = ImageSanitizerService._copiarSomentePixels(orientada, formato)

        saida = io.BytesIO()
        if formato == "PNG":
            limpa.save(saida, format="PNG", optimize=True)
        else:
            limpa.save(saida, format=formato, quality=QUALIDADE_JPEG_WEBP)
        sanitizado = saida.getvalue()

        return ImagemSanitizada(
            conteudo=sanitizado,
            extensao=FORMATOS_PERMITIDOS[formato],
            sha256=hashlib.sha256(sanitizado).hexdigest()
        )

    @staticmethod
    def _copiarSomentePixels(imagem: Image.Image, formato: str) -> Image.Image:
        """Cria uma imagem nova a partir dos pixels, sem herdar `info` (EXIF, XMP, ICC, textos)."""
        temTransparencia = imagem.mode in ("RGBA", "LA", "PA") or "transparency" in imagem.info
        if formato == "JPEG":
            modoAlvo = "L" if imagem.mode == "L" else "RGB"
        elif temTransparencia or imagem.mode == "P":
            modoAlvo = "RGBA"
        else:
            modoAlvo = "L" if imagem.mode == "L" else "RGB"

        convertida = imagem.convert(modoAlvo)
        return Image.frombytes(modoAlvo, convertida.size, convertida.tobytes())
