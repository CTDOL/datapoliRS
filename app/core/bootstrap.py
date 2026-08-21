import logging
from app.core.config import settings
from app.core.database import getDatabaseConnection
from app.services.auth_service import AuthService

logger = logging.getLogger("Bootstrap")


async def ensureAdminUser() -> None:
    """Garante que o usuário administrador (ADMIN_EMAIL) exista no banco. Idempotente."""
    hashedPassword = AuthService.get_password_hash(settings.ADMIN_PASSWORD)
    async for connection in getDatabaseConnection():
        await connection.execute(
            """
            INSERT INTO tb_users (tenant_id, email, hashed_password, is_active)
            VALUES ($1, $2, $3, TRUE)
            ON CONFLICT (email) DO NOTHING
            """,
            settings.ADMIN_TENANT_ID,
            settings.ADMIN_EMAIL,
            hashedPassword,
        )
    logger.info(f"Usuário administrador garantido: {settings.ADMIN_EMAIL}")
