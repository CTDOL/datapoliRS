from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.dependencies import require_role, bloquear_super_admin
from app.core.rate_limit import RateLimiter
from app.schemas.email import EmailTesteRequest
from app.schemas.user import UserInDB
from app.services.email_service import EmailService, EmailNaoConfiguradoError

# Rótulo do ambiente no assunto e no corpo. ENVIRONMENT vem do arquivo de ambiente de cada compose.
ROTULOS_AMBIENTE = {"development": "DEV", "hml": "HML", "production": "PRD"}

router = APIRouter(
    prefix="/api/v1/gabinete/email",
    tags=["Configurações do Gabinete"],
    dependencies=[Depends(RateLimiter(times=5, seconds=60, configKey="email_teste")), Depends(bloquear_super_admin)]
)


@router.post(
    "/teste",
    status_code=status.HTTP_200_OK,
    summary="Envia um e-mail de teste ao destinatário informado (verifica a configuração SMTP)"
)
async def enviar_email_teste(
    payload: EmailTesteRequest,
    current_user: UserInDB = Depends(require_role(["admin"]))
) -> dict:
    rotulo = ROTULOS_AMBIENTE.get(settings.ENVIRONMENT, settings.ENVIRONMENT.upper())
    corpo = (
        f"Este é um e-mail de teste do DATAPOLIRS.\n\n"
        f"Ambiente: {rotulo} ({settings.ENVIRONMENT})\n\n"
        "Se você recebeu esta mensagem, o envio de e-mail está funcionando neste ambiente."
    )
    try:
        await EmailService.enviar(payload.destinatario, f"[{rotulo}] Teste de envio — DATAPOLIRS", corpo)
    except EmailNaoConfiguradoError as erro:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(erro))
    except OSError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível conectar ao servidor de e-mail."
        )
    return {"enviado_para": payload.destinatario}
