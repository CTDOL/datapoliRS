"""FR-006: fotos de lideranças sem metadados EXIF/GPS e gravadas com hash determinístico."""
import io
import os
import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image, ExifTags, PngImagePlugin
from app.main import app
from app.routers.cabinet import UPLOADS_DIR
from app.services.image_sanitizer_service import ImageSanitizerService
from tests.test_sprint2_endpoints import bearerHeader

ORIENTACAO_ROTACIONAR_90 = 6
TAG_ORIENTACAO = 0x0112


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as testClient:
        yield testClient


def jpegComGps(largura: int = 40, altura: int = 20) -> bytes:
    """JPEG de celular simulado: GPS em Porto Alegre e orientação 'girar 90°'."""
    exif = Image.Exif()
    exif[TAG_ORIENTACAO] = ORIENTACAO_ROTACIONAR_90
    exif[ExifTags.Base.Make] = "Celular de Teste"
    exif[ExifTags.IFD.GPSInfo] = {
        ExifTags.GPS.GPSLatitudeRef: "S",
        ExifTags.GPS.GPSLatitude: (30.0, 2.0, 4.0),
        ExifTags.GPS.GPSLongitudeRef: "W",
        ExifTags.GPS.GPSLongitude: (51.0, 13.0, 3.0),
    }
    saida = io.BytesIO()
    Image.new("RGB", (largura, altura), (200, 30, 30)).save(saida, format="JPEG", exif=exif)
    return saida.getvalue()


def metadadosDe(conteudo: bytes) -> dict:
    with Image.open(io.BytesIO(conteudo)) as imagem:
        return {"exif": dict(imagem.getexif()), "info": dict(imagem.info), "size": imagem.size}


def test_jpeg_de_entrada_tem_gps():
    """Garante que o teste abaixo parte de uma foto que de fato carrega GPS."""
    with Image.open(io.BytesIO(jpegComGps())) as imagem:
        assert imagem.getexif().get_ifd(ExifTags.IFD.GPSInfo)


def test_sanitize_remove_exif_e_gps_e_aplica_orientacao():
    resultado = ImageSanitizerService.sanitize(jpegComGps(40, 20))
    meta = metadadosDe(resultado.conteudo)

    assert resultado.extensao == "jpg"
    assert meta["exif"] == {}
    assert "exif" not in meta["info"]
    # A orientação foi aplicada aos pixels antes do descarte: 40x20 virou 20x40.
    assert meta["size"] == (20, 40)


def test_sanitize_remove_texto_e_exif_de_png():
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "endereco da lideranca")
    saida = io.BytesIO()
    Image.new("RGBA", (10, 10), (0, 0, 255, 128)).save(saida, format="PNG", pnginfo=info)

    resultado = ImageSanitizerService.sanitize(saida.getvalue())
    meta = metadadosDe(resultado.conteudo)

    assert resultado.extensao == "png"
    assert "Comment" not in meta["info"]
    assert meta["exif"] == {}
    with Image.open(io.BytesIO(resultado.conteudo)) as imagem:
        assert imagem.mode == "RGBA"  # transparência preservada


def test_sanitize_hash_deterministico():
    entrada = jpegComGps()
    primeiro = ImageSanitizerService.sanitize(entrada)
    segundo = ImageSanitizerService.sanitize(entrada)
    assert primeiro.sha256 == segundo.sha256
    assert len(primeiro.sha256) == 64


def test_sanitize_rejeita_conteudo_que_nao_e_imagem():
    with pytest.raises(HTTPException) as erro:
        ImageSanitizerService.sanitize(b"<svg onload=alert(1)></svg>")
    assert erro.value.status_code == 415


def test_sanitize_rejeita_formato_fora_da_allowlist():
    saida = io.BytesIO()
    Image.new("RGB", (5, 5)).save(saida, format="GIF")
    with pytest.raises(HTTPException) as erro:
        ImageSanitizerService.sanitize(saida.getvalue())
    assert erro.value.status_code == 415


def test_sanitize_rejeita_resolucao_excessiva(monkeypatch):
    monkeypatch.setattr("app.services.image_sanitizer_service.MAX_PIXELS", 100)
    with pytest.raises(HTTPException) as erro:
        ImageSanitizerService.sanitize(jpegComGps(20, 20))
    assert erro.value.status_code == 413


def criarLideranca(client: TestClient, tenantId: str) -> str:
    resposta = client.post(
        "/api/v1/gabinete/liderancas",
        headers=bearerHeader(tenantId),
        json={"nm_completo": "Liderança com Foto", "municipios": ["4314902"]}
    )
    assert resposta.status_code == 201
    return resposta.json()["id_lideranca"]


def enviarFoto(client: TestClient, tenantId: str, idLideranca: str, conteudo: bytes, contentType: str = "image/jpeg"):
    return client.post(
        f"/api/v1/gabinete/liderancas/{idLideranca}/foto",
        headers=bearerHeader(tenantId),
        files={"arquivo": ("foto.jpg", conteudo, contentType)}
    )


def test_upload_grava_foto_sem_gps_com_hash_no_nome(client: TestClient):
    tenantId = str(uuid.uuid4())
    idLideranca = criarLideranca(client, tenantId)

    resposta = enviarFoto(client, tenantId, idLideranca, jpegComGps())
    assert resposta.status_code == 200
    fotoUrl = resposta.json()["ds_foto_url"]
    nomeArquivo = os.path.basename(fotoUrl)
    assert nomeArquivo.startswith(f"{idLideranca}-") and nomeArquivo.endswith(".jpg")

    caminho = os.path.join(UPLOADS_DIR, nomeArquivo)
    with open(caminho, "rb") as arquivo:
        assert metadadosDe(arquivo.read())["exif"] == {}

    # Nova foto substitui a anterior: o arquivo antigo some do disco.
    outra = enviarFoto(client, tenantId, idLideranca, jpegComGps(30, 30))
    assert outra.status_code == 200
    assert not os.path.exists(caminho)
    caminhoNovo = os.path.join(UPLOADS_DIR, os.path.basename(outra.json()["ds_foto_url"]))
    assert os.path.exists(caminhoNovo)

    # Excluir a liderança remove a foto do disco.
    assert client.delete(f"/api/v1/gabinete/liderancas/{idLideranca}", headers=bearerHeader(tenantId)).status_code == 204
    assert not os.path.exists(caminhoNovo)


def test_upload_rejeita_conteudo_falso_com_content_type_de_imagem(client: TestClient):
    tenantId = str(uuid.uuid4())
    idLideranca = criarLideranca(client, tenantId)

    resposta = enviarFoto(client, tenantId, idLideranca, b"<html><script>alert(1)</script></html>")
    assert resposta.status_code == 415
    assert not [f for f in os.listdir(UPLOADS_DIR) if f.startswith(idLideranca)]

    client.delete(f"/api/v1/gabinete/liderancas/{idLideranca}", headers=bearerHeader(tenantId))


def test_upload_de_outro_gabinete_nao_grava_arquivo(client: TestClient):
    tenantA = str(uuid.uuid4())
    tenantB = str(uuid.uuid4())
    idLideranca = criarLideranca(client, tenantA)

    resposta = enviarFoto(client, tenantB, idLideranca, jpegComGps())
    assert resposta.status_code == 404
    assert not [f for f in os.listdir(UPLOADS_DIR) if f.startswith(idLideranca)]

    client.delete(f"/api/v1/gabinete/liderancas/{idLideranca}", headers=bearerHeader(tenantA))
