"""Comentários de execução das tarefas do gabinete

Revision ID: m3b4c5d6e7f8
Revises: l2a3b4c5d6e7
Create Date: 2026-10-23 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'm3b4c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = 'l2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_gabinete_tarefa_comentarios (
            id_comentario UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant) ON DELETE CASCADE,
            id_tarefa UUID NOT NULL REFERENCES tb_gabinete_tarefas(id_tarefa) ON DELETE CASCADE,
            autor_email VARCHAR(255) NOT NULL,
            texto TEXT NOT NULL CHECK (char_length(texto) BETWEEN 1 AND 2000),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_comentarios_tarefa ON tb_gabinete_tarefa_comentarios (id_tarefa, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_comentarios_tenant_data ON tb_gabinete_tarefa_comentarios (tenant_id, created_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tb_gabinete_tarefa_comentarios")
