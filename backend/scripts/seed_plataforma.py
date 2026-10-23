"""Cria o gabinete da plataforma e a conta do super-admin (ADR 037).

Idempotente: rodar de novo não duplica nada e não troca a senha.
Recusa rodar fora do banco de desenvolvimento (datapoli_db em localhost).

Uso, a partir de backend/ (a senha vem do ambiente, nunca do código):
    PLATAFORMA_ADMIN_PASSWORD='...' PYTHONPATH=.. ../.venv/bin/python -m scripts.seed_plataforma
"""
import asyncio
import os
import sys

import asyncpg

from app.core.config import settings
from app.services.auth_service import AuthService
from app.services.plataforma_service import PLATAFORMA_TENANT_ID

NOME_PLATAFORMA = "CTDOL Plataforma"
CARGO_PLATAFORMA = "Plataforma"
EMAIL_SUPER_ADMIN = "desenvolvedor@ctdol.com.br"


def verificar_ambiente() -> None:
    if settings.ENVIRONMENT != "development":
        sys.exit(f"Recusado: ENVIRONMENT={settings.ENVIRONMENT}. O seed só roda em development.")
    if "@localhost:" not in settings.DATABASE_URL or not settings.DATABASE_URL.endswith("/datapoli_db"):
        sys.exit("Recusado: DATABASE_URL precisa apontar para localhost e para o banco datapoli_db.")


async def main() -> None:
    verificar_ambiente()

    senha = os.environ.get("PLATAFORMA_ADMIN_PASSWORD")
    if not senha:
        sys.exit("Defina PLATAFORMA_ADMIN_PASSWORD no ambiente antes de rodar.")

    hashed = AuthService.get_password_hash(senha)
    conexao = await asyncpg.connect(dsn=settings.DATABASE_URL)
    try:
        async with conexao.transaction():
            await conexao.execute(
                """
                INSERT INTO tb_tenants (id_tenant, nm_mandato, ds_cargo_mandato)
                VALUES ($1, $2, $3)
                ON CONFLICT (id_tenant) DO NOTHING
                """,
                PLATAFORMA_TENANT_ID, NOME_PLATAFORMA, CARGO_PLATAFORMA,
            )
            await conexao.execute(
                """
                INSERT INTO tb_users (tenant_id, email, hashed_password, is_active, role)
                VALUES ($1, $2, $3, TRUE, 'super_admin')
                ON CONFLICT (email) DO NOTHING
                """,
                PLATAFORMA_TENANT_ID, EMAIL_SUPER_ADMIN, hashed,
            )
    finally:
        await conexao.close()

    print(f"Plataforma: {NOME_PLATAFORMA} ({PLATAFORMA_TENANT_ID})")
    print(f"Super-admin: {EMAIL_SUPER_ADMIN}")


if __name__ == "__main__":
    asyncio.run(main())
