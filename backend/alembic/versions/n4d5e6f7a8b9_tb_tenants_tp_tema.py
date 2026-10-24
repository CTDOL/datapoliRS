"""tb_tenants: tema da interface claro ou escuro, por gabinete

Revision ID: n4d5e6f7a8b9
Revises: m3b4c5d6e7f8
Create Date: 2026-10-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'n4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'm3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Mudança aditiva (Expand). O default 'escuro' mantém a aparência atual dos gabinetes existentes."""
    op.execute("ALTER TABLE tb_tenants ADD COLUMN IF NOT EXISTS tp_tema VARCHAR(10) NOT NULL DEFAULT 'escuro'")
    op.execute("""
        ALTER TABLE tb_tenants
        ADD CONSTRAINT ck_tenants_tp_tema CHECK (tp_tema IN ('escuro', 'claro'))
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tb_tenants DROP CONSTRAINT IF EXISTS ck_tenants_tp_tema")
    op.execute("ALTER TABLE tb_tenants DROP COLUMN IF EXISTS tp_tema")
