"""role super_admin em tb_users (ADR 037)

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-10-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'h8c9d0e1f2a3'
down_revision: Union[str, Sequence[str], None] = 'g7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Amplia a restrição de papel para aceitar o super-admin da plataforma.

    Mudança aditiva (Expand): nenhum papel existente deixa de ser válido.
    """
    op.execute("ALTER TABLE tb_users DROP CONSTRAINT IF EXISTS ck_users_role")
    op.execute("""
        ALTER TABLE tb_users
        ADD CONSTRAINT ck_users_role CHECK (role IN ('super_admin', 'admin', 'operador', 'leitor'))
    """)


def downgrade() -> None:
    """Volta à restrição anterior. Falha se ainda existir usuário com papel super_admin."""
    op.execute("ALTER TABLE tb_users DROP CONSTRAINT IF EXISTS ck_users_role")
    op.execute("""
        ALTER TABLE tb_users
        ADD CONSTRAINT ck_users_role CHECK (role IN ('admin', 'operador', 'leitor'))
    """)
