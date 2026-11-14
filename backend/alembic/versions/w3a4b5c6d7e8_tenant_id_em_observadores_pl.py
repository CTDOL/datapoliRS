"""tenant_id em tb_gabinete_projeto_lei_observadores (Issue #42 / M6)

Revision ID: w3a4b5c6d7e8
Revises: v2f3a4b5c6d7
Create Date: 2026-11-13 22:58:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "w3a4b5c6d7e8"
down_revision: Union[str, Sequence[str], None] = "v2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona tenant_id em tb_gabinete_projeto_lei_observadores com backfill (Expand, Regra 12.2)."""
    op.execute(
        """
        ALTER TABLE tb_gabinete_projeto_lei_observadores
        ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tb_tenants(id_tenant) ON DELETE CASCADE
        """
    )
    op.execute(
        """
        UPDATE tb_gabinete_projeto_lei_observadores o
        SET tenant_id = p.tenant_id
        FROM tb_gabinete_projetos_lei p
        WHERE o.id_projeto_lei = p.id_projeto_lei
          AND o.tenant_id IS NULL
        """
    )
    op.execute(
        """
        ALTER TABLE tb_gabinete_projeto_lei_observadores
        ALTER COLUMN tenant_id SET NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pl_observadores_tenant
        ON tb_gabinete_projeto_lei_observadores(tenant_id)
        """
    )


def downgrade() -> None:
    """Remove tenant_id e índice de tb_gabinete_projeto_lei_observadores."""
    op.execute("DROP INDEX IF EXISTS idx_pl_observadores_tenant")
    op.execute("ALTER TABLE tb_gabinete_projeto_lei_observadores DROP COLUMN IF EXISTS tenant_id")
