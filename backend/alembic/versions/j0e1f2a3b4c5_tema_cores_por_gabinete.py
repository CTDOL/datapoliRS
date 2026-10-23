"""tb_tenants: cores do gabinete (ADR 038)

Revision ID: j0e1f2a3b4c5
Revises: i9d0e1f2a3b4
Create Date: 2026-10-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'j0e1f2a3b4c5'
down_revision: Union[str, Sequence[str], None] = 'i9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Mudança aditiva (Expand). NULL significa o padrão da plataforma."""
    op.execute("ALTER TABLE tb_tenants ADD COLUMN IF NOT EXISTS cor_primaria VARCHAR(7) NULL")
    op.execute("ALTER TABLE tb_tenants ADD COLUMN IF NOT EXISTS cor_secundaria VARCHAR(7) NULL")
    op.execute("""
        ALTER TABLE tb_tenants
        ADD CONSTRAINT ck_tenants_cor_primaria CHECK (cor_primaria IS NULL OR cor_primaria ~ '^#[0-9A-Fa-f]{6}$')
    """)
    op.execute("""
        ALTER TABLE tb_tenants
        ADD CONSTRAINT ck_tenants_cor_secundaria CHECK (cor_secundaria IS NULL OR cor_secundaria ~ '^#[0-9A-Fa-f]{6}$')
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tb_tenants DROP CONSTRAINT IF EXISTS ck_tenants_cor_secundaria")
    op.execute("ALTER TABLE tb_tenants DROP CONSTRAINT IF EXISTS ck_tenants_cor_primaria")
    op.execute("ALTER TABLE tb_tenants DROP COLUMN IF EXISTS cor_secundaria")
    op.execute("ALTER TABLE tb_tenants DROP COLUMN IF EXISTS cor_primaria")
