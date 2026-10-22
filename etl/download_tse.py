import logging
import os
import shutil
import urllib.request

logger = logging.getLogger("ETL_DownloadTSE")

DATA_DIR = os.path.join("etl", "data")
TAMANHO_BLOCO = 1024 * 1024

URLS_TSE = {
    "votacao": "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip",
    "comparecimento": "https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_munzona/detalhe_votacao_munzona_{ano}.zip",
}

NOMES_ZIP = {
    "votacao": "votacao_{ano}.zip",
    "comparecimento": "detalhe_votacao_munzona_{ano}.zip",
}


def caminhoZip(tipo: str, ano: int) -> str:
    if tipo not in NOMES_ZIP:
        raise ValueError(f"Tipo de carga desconhecido: {tipo}")
    return os.path.join(DATA_DIR, NOMES_ZIP[tipo].format(ano=ano))


def baixarZipTse(tipo: str, ano: int, timeout: int = 900) -> str:
    """Garante o ZIP nacional do TSE em etl/data/. Se já existir, não baixa de novo.

    Baixa para um arquivo temporário e só renomeia ao terminar, para uma queda
    no meio do download não deixar um ZIP incompleto com o nome final."""
    destino = caminhoZip(tipo, ano)
    if os.path.exists(destino):
        return destino
    os.makedirs(DATA_DIR, exist_ok=True)
    url = URLS_TSE[tipo].format(ano=ano)
    temporario = destino + ".part"
    logger.info(f"Baixando {url} ...")
    with urllib.request.urlopen(url, timeout=timeout) as resposta, open(temporario, "wb") as arquivo:
        shutil.copyfileobj(resposta, arquivo, TAMANHO_BLOCO)
    os.replace(temporario, destino)
    logger.info(f"Download concluído: {destino}")
    return destino
