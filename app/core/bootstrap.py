import logging
from app.core.config import settings
from app.core.database import getDatabaseConnection
from app.services.auth_service import AuthService

logger = logging.getLogger("Bootstrap")


async def ensureAdminUser() -> None:
    """Garante que o tenant e o usuário administrador (ADMIN_EMAIL) existam no banco. Idempotente.

    tb_users.tenant_id tem FK obrigatória para tb_tenants: numa instalação nova,
    a tabela ainda está vazia neste ponto, então o tenant de bootstrap precisa
    ser criado aqui antes do usuário — não dá para depender só do backfill da
    migration (que só cobre tenant_id que já existiam em dados anteriores).
    """
    hashedPassword = AuthService.get_password_hash(settings.ADMIN_PASSWORD)
    async for connection in getDatabaseConnection():
        await connection.execute(
            """
            INSERT INTO tb_tenants (id_tenant, nm_mandato, ds_cargo_mandato)
            VALUES ($1, 'Gabinete Padrão', 'Não especificado')
            ON CONFLICT (id_tenant) DO NOTHING
            """,
            settings.ADMIN_TENANT_ID,
        )
        await connection.execute(
            """
            INSERT INTO tb_users (tenant_id, email, hashed_password, is_active, role)
            VALUES ($1, $2, $3, TRUE, 'admin')
            ON CONFLICT (email) DO UPDATE SET role = 'admin'
            """,
            settings.ADMIN_TENANT_ID,
            settings.ADMIN_EMAIL,
            hashedPassword,
        )
    logger.info(f"Tenant e usuário administrador garantidos: {settings.ADMIN_EMAIL}")
