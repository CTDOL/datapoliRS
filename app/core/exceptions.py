import logging
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
import asyncpg

logger = logging.getLogger("ExceptionHandler")


class DomainException(Exception):
    """Exceção base para regras de negócio do domínio CTDOL."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST, title: str = "Regra de Negócio Violada"):
        self.detail = detail
        self.status_code = status_code
        self.title = title
        super().__init__(detail)


def _build_rfc7807_response(
    status_code: int,
    title: str,
    detail: str,
    request: Request,
    error_type: str = "about:blank"
) -> JSONResponse:
    """Monta a resposta seguindo o padrão RFC 7807 Problem Details."""
    payload = {
        "type": error_type,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path)
    }
    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type="application/problem+json"
    )


async def asyncpg_unique_violation_handler(request: Request, exc: asyncpg.exceptions.UniqueViolationError) -> JSONResponse:
    """Captura violações de integridade Unique (ex: cadastro duplicado)."""
    logger.warning(f"UniqueViolationError na rota {request.url.path}: {str(exc)}")
    return _build_rfc7807_response(
        status_code=status.HTTP_409_CONFLICT,
        title="Conflito de Dados (Registro Duplicado)",
        detail="O registro que você está tentando criar já existe no sistema.",
        request=request,
        error_type="https://datapolirs.com.br/errors/unique-violation"
    )


async def asyncpg_fk_violation_handler(request: Request, exc: asyncpg.exceptions.ForeignKeyViolationError) -> JSONResponse:
    """Captura violações de chave estrangeira (ex: dependência não encontrada)."""
    logger.warning(f"ForeignKeyViolationError na rota {request.url.path}: {str(exc)}")
    return _build_rfc7807_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Violação de Referência",
        detail="O registro faz referência a um dado que não existe no sistema.",
        request=request,
        error_type="https://datapolirs.com.br/errors/fk-violation"
    )


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """Captura regras de negócio e validações customizadas do domínio."""
    logger.warning(f"DomainException na rota {request.url.path}: {exc.detail}")
    return _build_rfc7807_response(
        status_code=exc.status_code,
        title=exc.title,
        detail=exc.detail,
        request=request,
        error_type="https://datapolirs.com.br/errors/domain-logic"
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all para erros inesperados (500 Internal Server Error)."""
    logger.error(f"Erro Não Tratado na rota {request.url.path}: {str(exc)}", exc_info=True)
    return _build_rfc7807_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Erro Interno Inesperado",
        detail="Ocorreu um erro catastrófico no servidor. A equipe técnica já foi notificada.",
        request=request,
        error_type="https://datapolirs.com.br/errors/internal-server-error"
    )


def register_exception_handlers(app: Any) -> None:
    """Registra todos os manipuladores globais na aplicação FastAPI."""
    app.add_exception_handler(asyncpg.exceptions.UniqueViolationError, asyncpg_unique_violation_handler)
    app.add_exception_handler(asyncpg.exceptions.ForeignKeyViolationError, asyncpg_fk_violation_handler)
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
