"""cd_cargo_em_tb_tenants

Revision ID: ae5bbe065aec
Revises: fb903633c34c
Create Date: 2026-08-24 00:00:58.641389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae5bbe065aec'
down_revision: Union[str, Sequence[str], None] = 'fb903633c34c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona cd_cargo (FK para tb_cargos) em tb_tenants.

    ds_cargo_mandato (texto livre) é mantido para não quebrar o bootstrap
    e dados já existentes — o endpoint de atualização de perfil passa a
    manter os dois em sincronia sempre que cd_cargo é informado.
    """
    op.execute("""
        ALTER TABLE tb_tenants
        ADD COLUMN IF NOT EXISTS cd_cargo INT REFERENCES tb_cargos(cd_cargo)
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tb_tenants DROP COLUMN IF EXISTS cd_cargo")
