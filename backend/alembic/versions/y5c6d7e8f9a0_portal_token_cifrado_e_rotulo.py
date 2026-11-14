"""Adiciona rótulo opcional e token cifrado em tb_balcao_portais

Revision ID: y5c6d7e8f9a0
Revises: x4b5c6d7e8f9
Create Date: 2026-11-14 09:05:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'y5c6d7e8f9a0'
down_revision: Union[str, Sequence[str], None] = 'x4b5c6d7e8f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE tb_balcao_portais ADD COLUMN IF NOT EXISTS rotulo TEXT NULL")
    op.execute("ALTER TABLE tb_balcao_portais ADD COLUMN IF NOT EXISTS token_cifrado TEXT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE tb_balcao_portais DROP COLUMN IF EXISTS token_cifrado")
    op.execute("ALTER TABLE tb_balcao_portais DROP COLUMN IF EXISTS rotulo")
