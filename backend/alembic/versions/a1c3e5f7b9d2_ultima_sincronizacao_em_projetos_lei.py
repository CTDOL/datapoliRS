"""ultima_sincronizacao em tb_gabinete_projetos_lei

Revision ID: a1c3e5f7b9d2
Revises: 895f8ce12277
Create Date: 2026-09-16 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c3e5f7b9d2'
down_revision: Union[str, Sequence[str], None] = '895f8ce12277'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Carimba quando a situação do projeto de lei foi conferida pela última vez
    na fonte oficial. Importação e ressincronização atualizam o campo; o painel
    mostra "conferido há N dias" e permite atualizar sem apagar observadores e
    tarefas. Expand-only: coluna nula, backfill = created_at (a importação
    revalida na fonte, então created_at é a última conferência conhecida)."""
    op.execute("""
        ALTER TABLE tb_gabinete_projetos_lei
        ADD COLUMN IF NOT EXISTS ultima_sincronizacao TIMESTAMP WITH TIME ZONE
    """)
    op.execute("""
        UPDATE tb_gabinete_projetos_lei
        SET ultima_sincronizacao = created_at
        WHERE ultima_sincronizacao IS NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tb_gabinete_projetos_lei DROP COLUMN IF EXISTS ultima_sincronizacao")
