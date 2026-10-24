"""Cria o gabinete de demonstração da Deputada Estadual Delegada Nadine e o seu administrador.

Só o gabinete e o usuário admin: lideranças, emendas e projetos são cadastrados
pela própria tela. Idempotente: rodar de novo não duplica nada e não troca a senha.
Recusa rodar fora do banco de desenvolvimento (datapoli_db em localhost).

Uso, a partir de backend/ (a senha vem do ambiente, nunca do código):
    DEMO_ADMIN_PASSWORD='...' PYTHONPATH=.. ../.venv/bin/python -m scripts.seed_demo_gabinete
"""
import asyncio
import os
import sys
import uuid

import asyncpg

from app.core.config import settings
from app.services.auth_service import AuthService

NOME_GABINETE = "Gabinete Deputada Estadual Delegada Nadine"
CARGO = "Deputada Estadual"
MUNICIPIO_BASE = "4314902"  # Porto Alegre: centro da Visão Cruzada
EMAIL_ADMIN = "nadine.demo@campanha.com.br"
# UUID determinístico: o mesmo gabinete em qualquer execução.
TENANT_ID = uuid.uuid5(uuid.NAMESPACE_URL, "datapolirs:gabinete-demo-nadine")


def verificar_ambiente() -> None:
    if settings.ENVIRONMENT != "development":
        sys.exit(f"Recusado: ENVIRONMENT={settings.ENVIRONMENT}. O seed só roda em development.")
    if "@localhost:" not in settings.DATABASE_URL or not settings.DATABASE_URL.endswith("/datapoli_db"):
        sys.exit("Recusado: DATABASE_URL precisa apontar para localhost e para o banco datapoli_db.")


async def main() -> None:
    verificar_ambiente()

    senha = os.environ.get("DEMO_ADMIN_PASSWORD")
    if not senha:
        sys.exit("Defina DEMO_ADMIN_PASSWORD no ambiente antes de rodar.")

    hashed = AuthService.get_password_hash(senha)
    conexao = await asyncpg.connect(dsn=settings.DATABASE_URL)
    try:
        async with conexao.transaction():
            await conexao.execute(
                """
                INSERT INTO tb_tenants (id_tenant, nm_mandato, ds_cargo_mandato, cd_ibge_base)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id_tenant) DO NOTHING
                """,
                TENANT_ID,
                NOME_GABINETE,
                CARGO,
                MUNICIPIO_BASE,
            )
            await conexao.execute(
                """
                INSERT INTO tb_users (tenant_id, email, hashed_password, is_active, role)
                VALUES ($1, $2, $3, TRUE, 'admin')
                ON CONFLICT (email) DO NOTHING
                """,
                TENANT_ID,
                EMAIL_ADMIN,
                hashed,
            )
    finally:
        await conexao.close()

    print(f"Gabinete: {NOME_GABINETE} ({TENANT_ID})")
    print(f"Administrador: {EMAIL_ADMIN}")


if __name__ == "__main__":
    asyncio.run(main())
