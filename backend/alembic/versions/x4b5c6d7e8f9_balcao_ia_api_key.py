"""Chave de API cifrada do motor de extração IA do Balcão Inteligente

Revision ID: x4b5c6d7e8f9
Revises: w3a4b5c6d7e8
Create Date: 2026-11-13 23:25:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'x4b5c6d7e8f9'
down_revision: Union[str, Sequence[str], None] = 'w3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CHAVE = 'balcao.ia.api_key'
DESCRICAO = 'Chave de API cifrada do provedor de IA do Balcão (vazio usa BALCAO_IA_API_KEY do ambiente)'


def upgrade() -> None:
    op.execute(
        "INSERT INTO tb_configuracoes_sistema (chave, valor, tipo, categoria, descricao) "
        f"VALUES ('{CHAVE}', '', 'string', 'balcao_ia', '{DESCRICAO}') "
        "ON CONFLICT (chave) DO NOTHING"
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM tb_configuracoes_sistema WHERE chave = '{CHAVE}'")
