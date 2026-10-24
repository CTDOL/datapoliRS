import time
import hashlib
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

        # O IP é o do cliente real quando a API confia no proxy (FORWARDED_ALLOW_IPS no compose).
        # Nada que o cliente escolha entra na chave: um header como X-Tenant-ID zeraria o limite.
        client_ip = request.client.host if request.client else "unknown"
        escopo = self.configKey or "geral"

        # Janela de tempo baseada em timestamp fixo; o escopo separa o contador de cada rota.
        window_id = int(time.time() / seconds)
        cache_key = f"rate_limit:{escopo}:{client_ip}:{window_id}"

        try:
            # INCR atômico
            requests_count = await redisClientInstance.incr(cache_key)

            # Garante que a chave expire após a janela (com margem de segurança)
            if requests_count == 1:
                await redisClientInstance.expire(cache_key, seconds * 2)

            if requests_count > times:
                logger.warning(f"Rate limit excedido por IP={client_ip} / Escopo={escopo}")
                raise RateLimitExceededException(limit=times, window=seconds)

        except RateLimitExceededException:
            raise
        except Exception as e:
            logger.warning(f"Falha de resiliência no Rate Limiter (liberando tráfego): {e}")


class LimitePorConta:
    """Limite de falhas de login por conta, independente do IP de origem.

    O limite por IP não segura um ataque distribuído contra uma conta. Este conta as falhas
    de cada e-mail numa janela que começa na primeira falha; atingido o teto, o login daquela
    conta responde 429 até a janela acabar, mesmo com a senha certa. O login certo zera a conta.
    A chave guarda o hash do e-mail, não o e-mail. Fail-open se o Redis estiver indisponível.
    """

    def __init__(self, times: int = 10, seconds: int = 900, configKey: str = "login_conta"):
        self.times = times
        self.seconds = seconds
        self.configKey = configKey

    def _chave(self, conta: str) -> str:
        digest = hashlib.sha256(conta.strip().lower().encode()).hexdigest()
        return f"rate_limit:conta:{self.configKey}:{digest}"

    async def _limites(self) -> tuple[int, int]:
        from app.services.system_config_service import SystemConfigService
        times = await SystemConfigService.getIntFromCacheOnly(f"rate_limit.{self.configKey}.times", self.times)
        seconds = await SystemConfigService.getIntFromCacheOnly(f"rate_limit.{self.configKey}.seconds", self.seconds)
        return times, seconds

    async def verificar(self, conta: str) -> None:
        from app.core.redis_client import redisClientInstance
        if redisClientInstance is None:
            return
        times, seconds = await self._limites()
        try:
            falhas = await redisClientInstance.get(self._chave(conta))
        except Exception as e:
            logger.warning(f"Falha de resiliência no limite por conta (liberando): {e}")
            return
        if falhas is not None and int(falhas) >= times:
            logger.warning("Limite de falhas de login por conta atingido.")
            raise RateLimitExceededException(limit=times, window=seconds)

    async def registrarFalha(self, conta: str) -> None:
        from app.core.redis_client import redisClientInstance
        if redisClientInstance is None:
            return
        _, seconds = await self._limites()
        chave = self._chave(conta)
        try:
            if await redisClientInstance.incr(chave) == 1:
                await redisClientInstance.expire(chave, seconds)
        except Exception as e:
            logger.warning(f"Falha de resiliência no limite por conta (falha não contada): {e}")

    async def limpar(self, conta: str) -> None:
        from app.core.redis_client import redisClientInstance
        if redisClientInstance is None:
            return
        try:
            await redisClientInstance.delete(self._chave(conta))
        except Exception as e:
            logger.warning(f"Falha de resiliência no limite por conta (contador mantido): {e}")
