"""Cria o gabinete da plataforma e a conta do super-admin (ADR 037).

Idempotente: rodar de novo não duplica nada e não troca a senha.

Dois modos. Em ambos a senha fica fora do código.
- Desenvolvimento (padrão): recusa rodar fora do banco de desenvolvimento (datapoli_db em localhost).
  A senha vem de PLATAFORMA_ADMIN_PASSWORD.
- Produção (--producao): recusa rodar fora de ENVIRONMENT=production e do host interno postgres.
  A senha vem da entrada padrão (stdin), com no mínimo 12 caracteres.

Uso em desenvolvimento, a partir de backend/:
    PLATAFORMA_ADMIN_PASSWORD='...' PYTHONPATH=.. ../.venv/bin/python -m scripts.seed_plataforma

Uso em produção, dentro do container api (ver Plano Mestre v0.2.0, Passo 6):
    printf '%s\n' "$SENHA" | python -m scripts.seed_plataforma --producao
"""
import argparse
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
TAMANHO_MINIMO_SENHA_PRODUCAO = 12


def interpretar_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cria o gabinete da plataforma e o super-admin (ADR 037).")
    parser.add_argument("--producao", action="store_true", help="Roda no banco de produção; a senha vem do stdin.")
    return parser.parse_args()


def verificar_ambiente(producao: bool) -> None:
    if producao:
        if settings.ENVIRONMENT != "production":
            sys.exit(f"Recusado: ENVIRONMENT={settings.ENVIRONMENT}. O modo --producao só roda em production.")
        if "@postgres:" not in settings.DATABASE_URL:
            sys.exit("Recusado: DATABASE_URL precisa apontar para o host interno postgres (rede Docker de produção).")
        return
    if settings.ENVIRONMENT != "development":
        sys.exit(f"Recusado: ENVIRONMENT={settings.ENVIRONMENT}. O seed só roda em development.")
    if "@localhost:" not in settings.DATABASE_URL or not settings.DATABASE_URL.endswith("/datapoli_db"):
        sys.exit("Recusado: DATABASE_URL precisa apontar para localhost e para o banco datapoli_db.")


def obter_senha(producao: bool) -> str:
    if producao:
        senha = sys.stdin.readline().rstrip("\r\n")
        if len(senha) < TAMANHO_MINIMO_SENHA_PRODUCAO:
            sys.exit(f"ERRO FATAL: Senha recebida via stdin é menor que {TAMANHO_MINIMO_SENHA_PRODUCAO} caracteres.")
        return senha
    senha = os.environ.get("PLATAFORMA_ADMIN_PASSWORD")
    if not senha:
        sys.exit("Defina PLATAFORMA_ADMIN_PASSWORD no ambiente antes de rodar.")
    return senha


async def main() -> None:
    args = interpretar_argumentos()
    verificar_ambiente(args.producao)
    senha = obter_senha(args.producao)

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
                INSERT INTO tb_users (tenant_id, email, hashed_password, is_active, role, must_change_password)
                VALUES ($1, $2, $3, TRUE, 'super_admin', TRUE)
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
