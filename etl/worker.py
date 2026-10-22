"""Worker de cargas do ETL eleitoral. Consome tb_job_etl em loop, um job por vez.

Uso: python -m etl.worker
"""
import logging
import os
import time

import redis

from etl.download_tse import baixarZipTse
from etl.ingest_comparecimento import carregarComparecimento
from etl.ingest_tse import carregarVotacao
from etl.jobs import concluirJob, encerrarJobsOrfaos, reivindicarProximo

logger = logging.getLogger("ETL_Worker")

INTERVALO_SEGUNDOS = 5

CARGAS = {
    "votacao": carregarVotacao,
    "comparecimento": carregarComparecimento,
}


CHAVES_CACHE_ELEITORAL = ["electoral:eleicoes:list", "electoral:cargos:list"]


def invalidarCacheEleitoral() -> None:
    """Sem isso a lista de pleitos da API continua antiga até o TTL (1 h) expirar."""
    try:
        cliente = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        cliente.delete(*CHAVES_CACHE_ELEITORAL)
    except redis.RedisError as erro:
        logger.warning(f"Não foi possível invalidar o cache eleitoral: {erro}")


def processarJob(job: dict) -> bool:
    """Baixa o ZIP se preciso, executa a carga e registra o resultado do job. Retorna True se deu certo."""
    tipo, ano, idJob = job["tipo"], job["ano_eleicao"], job["id_job"]
    try:
        baixarZipTse(tipo, ano)
        CARGAS[tipo](ano)
        concluirJob(idJob, sucesso=True)
        invalidarCacheEleitoral()
        logger.info(f"Job {idJob} concluído ({tipo} {ano})")
        return True
    except Exception as erro:
        concluirJob(idJob, sucesso=False, erro=str(erro)[:2000])
        logger.error(f"Job {idJob} falhou ({tipo} {ano}): {erro}", exc_info=True)
        return False


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    orfaos = encerrarJobsOrfaos()
    if orfaos:
        logger.warning(f"{orfaos} job(s) órfão(s) marcado(s) como falha ao iniciar")
    logger.info("Worker de cargas ETL iniciado")
    while True:
        job = reivindicarProximo()
        if job is None:
            time.sleep(INTERVALO_SEGUNDOS)
            continue
        processarJob(job)


if __name__ == "__main__":
    main()
