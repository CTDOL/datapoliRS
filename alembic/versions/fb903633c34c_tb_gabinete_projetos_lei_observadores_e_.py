"""tb_gabinete_projetos_lei observadores e tarefas

Revision ID: fb903633c34c
Revises: 1dac719b2ee7
Create Date: 2026-08-23 09:31:14.915560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb903633c34c'
down_revision: Union[str, Sequence[str], None] = '1dac719b2ee7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria tb_gabinete_projetos_lei, tabela de observadores e tb_gabinete_tarefas.

    identificador_externo + UNIQUE(tenant_id, fonte, identificador_externo) garante
    que importar o mesmo PL da mesma fonte duas vezes seja idempotente (ON CONFLICT
    no repositório, não erro).
    """
    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_gabinete_projetos_lei (
            id_projeto_lei UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant) ON DELETE CASCADE,
            fonte VARCHAR(20) NOT NULL,
            identificador_externo VARCHAR(120) NOT NULL,
            tipo VARCHAR(20),
            numero VARCHAR(20),
            ano INT,
            ementa TEXT NOT NULL,
            situacao TEXT,
            autor VARCHAR(255),
            url_fonte TEXT,
            data_apresentacao DATE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE (tenant_id, fonte, identificador_externo)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_projetos_lei_tenant ON tb_gabinete_projetos_lei(tenant_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_gabinete_projeto_lei_observadores (
            id_projeto_lei UUID NOT NULL REFERENCES tb_gabinete_projetos_lei(id_projeto_lei) ON DELETE CASCADE,
            id_lideranca UUID NOT NULL REFERENCES tb_gabinete_liderancas(id_lideranca) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (id_projeto_lei, id_lideranca)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_gabinete_tarefas (
            id_tarefa UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant) ON DELETE CASCADE,
            id_projeto_lei UUID REFERENCES tb_gabinete_projetos_lei(id_projeto_lei) ON DELETE CASCADE,
            id_emenda UUID REFERENCES tb_gabinete_emendas(id_emenda) ON DELETE CASCADE,
            id_lideranca_responsavel UUID REFERENCES tb_gabinete_liderancas(id_lideranca),
            titulo VARCHAR(255) NOT NULL,
            descricao TEXT,
            prazo DATE,
            tp_status VARCHAR(20) NOT NULL DEFAULT 'Pendente',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_tarefas_tenant ON tb_gabinete_tarefas(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tarefas_projeto_lei ON tb_gabinete_tarefas(id_projeto_lei)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tarefas_emenda ON tb_gabinete_tarefas(id_emenda)")


def downgrade() -> None:
    """Remove tb_gabinete_tarefas, observadores e tb_gabinete_projetos_lei."""
    op.execute("DROP TABLE IF EXISTS tb_gabinete_tarefas")
    op.execute("DROP TABLE IF EXISTS tb_gabinete_projeto_lei_observadores")
    op.execute("DROP TABLE IF EXISTS tb_gabinete_projetos_lei")
