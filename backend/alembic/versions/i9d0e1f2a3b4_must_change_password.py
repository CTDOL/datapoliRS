"""tb_users.must_change_password: troca de senha obrigatória (ADR 037)

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-10-23 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'i9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = 'h8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Mudança aditiva (Expand): usuários existentes ficam com FALSE, sem troca forçada."""
    op.execute("""
        ALTER TABLE tb_users
        ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tb_users DROP COLUMN IF EXISTS must_change_password")
