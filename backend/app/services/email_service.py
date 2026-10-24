import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailNaoConfiguradoError(RuntimeError):
    """SMTP_HOST vazio: o envio está desligado neste ambiente."""


class EmailService:
    """Envio de e-mails transacionais via SMTP (stdlib, sem dependência nova)."""

    @staticmethod
    def _enviar_sincrono(destinatario: str, assunto: str, corpo: str) -> None:
        mensagem = EmailMessage()
        mensagem["From"] = settings.SMTP_FROM
        mensagem["To"] = destinatario
        mensagem["Subject"] = assunto
        mensagem.set_content(corpo)
        # Porta 465 usa TLS desde a conexão (SMTPS). Outras portas usam STARTTLS quando o servidor oferece.
        if settings.SMTP_PORT == 465:
            conexao = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            conexao = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            if conexao.has_extn("starttls"):
                conexao.starttls()
        with conexao as smtp:
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(mensagem)

    @staticmethod
    async def enviar(destinatario: str, assunto: str, corpo: str) -> None:
        if not settings.SMTP_HOST:
            raise EmailNaoConfiguradoError("Envio de e-mail não configurado neste ambiente (SMTP_HOST vazio).")
        # smtplib bloqueia; roda em thread para não travar o event loop do FastAPI.
        await asyncio.to_thread(EmailService._enviar_sincrono, destinatario, assunto, corpo)
        logger.info("E-mail enviado para %s (assunto: %s).", destinatario, assunto)
