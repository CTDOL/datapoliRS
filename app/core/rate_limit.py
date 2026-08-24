import time
import logging
from typing import Optional
from fastapi import Request
from app.core.redis_client import redisClientInstance
from app.core.exceptions import DomainException

logger = logging.getLogger("RateLimiter")

class RateLimitExceededException(DomainException):
    def __init__(self, limit: int, window: int):
        super().__init__(
            detail=f"Muitas requisições. O limite de {limit} requisições a cada {window} segundo(s) foi excedido.",
            status_code=429,
            title="Too Many Requests"
        )


class RateLimiter:
    """Implementa Rate Limiting com Fixed Window no Redis.

    Quando configKey é informado, times/seconds passam a ser resolvidos a cada
    chamada a partir da configuração global editável em runtime (tela de
    administração) — a leitura é só-Redis (SystemConfigService.getIntFromCacheOnly),
    sem abrir conexão de banco no caminho quente. Os valores do construtor
    continuam valendo como fallback caso a configuração ainda não exista/aqueça.
    """

    def __init__(self, times: int = 20, seconds: int = 1, configKey: Optional[str] = None):
        self.times = times
        self.seconds = seconds
        self.configKey = configKey

    async def __call__(self, request: Request):
        from app.core.redis_client import redisClientInstance

        if redisClientInstance is None:
            return  # Fail-open se o Redis estiver indisponível

        times, seconds = self.times, self.seconds
        if self.configKey:
            from app.services.system_config_service import SystemConfigService
            times = await SystemConfigService.getIntFromCacheOnly(f"rate_limit.{self.configKey}.times", self.times)
            seconds = await SystemConfigService.getIntFromCacheOnly(f"rate_limit.{self.configKey}.seconds", self.seconds)

        client_ip = request.client.host if request.client else "unknown"
        tenant_id = request.headers.get("X-Tenant-ID", "public")

        # Janela de tempo baseada em timestamp fixo
        window_id = int(time.time() / seconds)
        cache_key = f"rate_limit:{tenant_id}:{client_ip}:{window_id}"

        try:
            # INCR atômico
            requests_count = await redisClientInstance.incr(cache_key)

            # Garante que a chave expire após a janela (com margem de segurança)
            if requests_count == 1:
                await redisClientInstance.expire(cache_key, seconds * 2)

            if requests_count > times:
                logger.warning(f"Rate limit excedido por IP={client_ip} / Tenant={tenant_id}")
                raise RateLimitExceededException(limit=times, window=seconds)

        except RateLimitExceededException:
            raise
        except Exception as e:
            logger.warning(f"Falha de resiliência no Rate Limiter (liberando tráfego): {e}")
