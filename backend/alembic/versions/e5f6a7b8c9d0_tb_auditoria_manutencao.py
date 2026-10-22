"""tb_auditoria_manutencao: registro de ações administrativas sobre dados eleitorais

Revision ID: e5f6a7b8c9d0
Revises: d8e2f3a4b5c6
Create Date: 2026-10-22 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd8e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Somente inserção. Guarda quem ativou qual pleito, quando e qual era o valor anterior."""
    op.execute("""
        CREATE TABLE tb_auditoria_manutencao (
            id_evento BIGSERIAL PRIMARY KEY,
            acao VARCHAR(40) NOT NULL,
            detalhe JSONB NOT NULL DEFAULT '{}'::jsonb,
            operador VARCHAR(255) NOT NULL,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tb_auditoria_manutencao;")
