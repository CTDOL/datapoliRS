"""tb_gabinete_tarefas.id_lideranca_responsavel: ON DELETE SET NULL (revisão de 2026-10-24, achado A3)

A tabela de vínculo da ADR 046 apaga em cascata, mas a coluna legada não tinha ação
na exclusão: excluir a liderança responsável por uma tarefa era recusado pelo banco.
A aplicação reaponta a coluna para o próximo responsável antes de excluir; esta FK é a
garantia no banco para qualquer outro caminho. Expand: a coluna continua existindo.

Revision ID: q7a8b9c0d1e2
Revises: p6e7f8a9b0c1
Create Date: 2026-10-24 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'q7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'p6e7f8a9b0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK = "tb_gabinete_tarefas_id_lideranca_responsavel_fkey"


def upgrade() -> None:
    op.execute(f"ALTER TABLE tb_gabinete_tarefas DROP CONSTRAINT IF EXISTS {FK}")
    op.execute(f"""
        ALTER TABLE tb_gabinete_tarefas
        ADD CONSTRAINT {FK} FOREIGN KEY (id_lideranca_responsavel)
        REFERENCES tb_gabinete_liderancas(id_lideranca) ON DELETE SET NULL
    """)


def downgrade() -> None:
    """Volta à FK original, sem ação na exclusão."""
    op.execute(f"ALTER TABLE tb_gabinete_tarefas DROP CONSTRAINT IF EXISTS {FK}")
    op.execute(f"""
        ALTER TABLE tb_gabinete_tarefas
        ADD CONSTRAINT {FK} FOREIGN KEY (id_lideranca_responsavel)
        REFERENCES tb_gabinete_liderancas(id_lideranca)
    """)
