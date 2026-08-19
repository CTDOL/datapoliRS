import time
import logging
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
    """Implementa Rate Limiting com Fixed Window no Redis."""
    
    def __init__(self, times: int = 20, seconds: int = 1):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request):
        from app.core.redis_client import redisClientInstance
        
        if redisClientInstance is None:
            return  # Fail-open se o Redis estiver indisponível
            
        client_ip = request.client.host if request.client else "unknown"
        tenant_id = request.headers.get("X-Tenant-ID", "public")
        
        # Janela de tempo baseada em timestamp fixo
        window_id = int(time.time() / self.seconds)
        cache_key = f"rate_limit:{tenant_id}:{client_ip}:{window_id}"
        
        try:
            # INCR atômico
            requests_count = await redisClientInstance.incr(cache_key)
            
            # Garante que a chave expire após a janela (com margem de segurança)
            if requests_count == 1:
                await redisClientInstance.expire(cache_key, self.seconds * 2)
                
            if requests_count > self.times:
                logger.warning(f"Rate limit excedido por IP={client_ip} / Tenant={tenant_id}")
                raise RateLimitExceededException(limit=self.times, window=self.seconds)
                
        except RateLimitExceededException:
            raise
        except Exception as e:
            logger.warning(f"Falha de resiliência no Rate Limiter (liberando tráfego): {e}")
