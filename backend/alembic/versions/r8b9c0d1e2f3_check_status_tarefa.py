"""tb_gabinete_tarefas.tp_status: CHECK com os status da ADR 046 (revisão de 2026-10-24, achado M7)

O domínio do status existia só no frontend: a API e o banco aceitavam qualquer texto, e uma
tarefa com status desconhecido sumia do quadro. Expand: NOT VALID, porque linhas antigas não
são checadas na criação da restrição e um valor fora do domínio já gravado não trava o deploy.
Linhas novas e alteradas passam a ser checadas. O VALIDATE CONSTRAINT fica para a contração,
depois de conferir que nenhuma linha antiga está fora do domínio.

Revision ID: r8b9c0d1e2f3
Revises: q7a8b9c0d1e2
Create Date: 2026-10-24 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'r8b9c0d1e2f3'
down_revision: Union[str, Sequence[str], None] = 'q7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CHECK = "ck_tarefas_tp_status"


def upgrade() -> None:
    op.execute(f"ALTER TABLE tb_gabinete_tarefas DROP CONSTRAINT IF EXISTS {CHECK}")
    op.execute(f"""
        ALTER TABLE tb_gabinete_tarefas
        ADD CONSTRAINT {CHECK}
        CHECK (tp_status IN ('Pendente', 'Em Andamento', 'Concluída', 'Cancelada')) NOT VALID
    """)


def downgrade() -> None:
    op.execute(f"ALTER TABLE tb_gabinete_tarefas DROP CONSTRAINT IF EXISTS {CHECK}")
