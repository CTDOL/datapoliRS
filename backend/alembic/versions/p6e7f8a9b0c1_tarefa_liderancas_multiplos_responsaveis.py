"""tb_gabinete_tarefa_liderancas: múltiplos responsáveis por tarefa (ADR 046, fase 1)

Revision ID: p6e7f8a9b0c1
Revises: o5e6f7a8b9c0
Create Date: 2026-10-24 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'p6e7f8a9b0c1'
down_revision: Union[str, Sequence[str], None] = 'o5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Expand: cria a tabela de vínculo e copia o responsável atual. A coluna id_lideranca_responsavel permanece."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_gabinete_tarefa_liderancas (
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant) ON DELETE CASCADE,
            id_tarefa UUID NOT NULL REFERENCES tb_gabinete_tarefas(id_tarefa) ON DELETE CASCADE,
            id_lideranca UUID NOT NULL REFERENCES tb_gabinete_liderancas(id_lideranca) ON DELETE CASCADE,
            PRIMARY KEY (id_tarefa, id_lideranca)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tarefa_liderancas_lideranca
        ON tb_gabinete_tarefa_liderancas (id_lideranca)
    """)
    # Backfill idempotente: copia o responsável único atual para a tabela de vínculo.
    op.execute("""
        INSERT INTO tb_gabinete_tarefa_liderancas (tenant_id, id_tarefa, id_lideranca)
        SELECT t.tenant_id, t.id_tarefa, t.id_lideranca_responsavel
        FROM tb_gabinete_tarefas t
        WHERE t.id_lideranca_responsavel IS NOT NULL
        ON CONFLICT (id_tarefa, id_lideranca) DO NOTHING
    """)


def downgrade() -> None:
    """Reverte só a tabela nova. A coluna antiga nunca foi alterada, então nenhum dado original se perde."""
    op.execute("DROP TABLE IF EXISTS tb_gabinete_tarefa_liderancas")
