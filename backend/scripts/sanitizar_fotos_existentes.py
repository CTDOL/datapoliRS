"""FR-006: remove EXIF/GPS das fotos de lideranças enviadas antes da sanitização no upload.

Regrava cada arquivo no mesmo nome, então as URLs gravadas em tb_liderancas
continuam válidas. Sem `--aplicar`, só lista o que faria.

Uso (a partir de backend/, ou de /app dentro do container da API):
    python -m scripts.sanitizar_fotos_existentes            # simulação
    python -m scripts.sanitizar_fotos_existentes --aplicar  # grava
"""
import argparse
import io
import os
import sys
from fastapi import HTTPException
from PIL import Image
from app.routers.cabinet import UPLOADS_DIR
from app.services.image_sanitizer_service import ImageSanitizerService


def temMetadados(conteudo: bytes) -> bool:
    with Image.open(io.BytesIO(conteudo)) as imagem:
        chavesSensiveis = {"exif", "xmp", "XML:com.adobe.xmp", "comment", "icc_profile"}
        return bool(imagem.getexif()) or bool(chavesSensiveis & set(imagem.info)) or \
            any(isinstance(valor, str) for valor in imagem.info.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--aplicar", action="store_true", help="grava as fotos sanitizadas (padrão: simulação)")
    args = parser.parse_args()

    if not os.path.isdir(UPLOADS_DIR):
        print(f"Diretório {UPLOADS_DIR} não existe; nada a fazer.")
        return 0

    sanitizadas, limpas, rejeitadas = 0, 0, 0
    for nome in sorted(os.listdir(UPLOADS_DIR)):
        caminho = os.path.join(UPLOADS_DIR, nome)
        if not os.path.isfile(caminho):
            continue
        with open(caminho, "rb") as arquivo:
            conteudo = arquivo.read()

        try:
            imagem = ImageSanitizerService.sanitize(conteudo)
        except HTTPException as erro:
            # Conteúdo que não é imagem válida ou formato diferente da extensão: não toca, só reporta.
            print(f"REJEITADA  {nome}: {erro.detail}")
            rejeitadas += 1
            continue

        extensaoAtual = nome.rsplit(".", 1)[-1].lower()
        if imagem.extensao != extensaoAtual:
            print(f"REJEITADA  {nome}: conteúdo é {imagem.extensao}, extensão é {extensaoAtual}")
            rejeitadas += 1
            continue

        if not temMetadados(conteudo):
            limpas += 1
            continue

        print(f"{'SANITIZADA' if args.aplicar else 'SANITIZAR '} {nome}")
        sanitizadas += 1
        if args.aplicar:
            temporario = caminho + ".tmp"
            with open(temporario, "wb") as destino:
                destino.write(imagem.conteudo)
            os.replace(temporario, caminho)  # troca atômica: nunca fica meio arquivo servido

    modo = "gravadas" if args.aplicar else "a sanitizar (simulação)"
    print(f"\nResumo: {sanitizadas} {modo}, {limpas} já sem metadados, {rejeitadas} rejeitadas.")
    return 1 if rejeitadas else 0


if __name__ == "__main__":
    sys.exit(main())
