"""tb_users: preferências pessoais persistidas no servidor

Revision ID: o5e6f7a8b9c0
Revises: n4d5e6f7a8b9
Create Date: 2026-10-24 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'o5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'n4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Mudança aditiva (Expand). '{}' significa usar o padrão de cada preferência."""
    op.execute("ALTER TABLE tb_users ADD COLUMN IF NOT EXISTS preferencias JSONB NOT NULL DEFAULT '{}'::jsonb")


def downgrade() -> None:
    op.execute("ALTER TABLE tb_users DROP COLUMN IF EXISTS preferencias")
