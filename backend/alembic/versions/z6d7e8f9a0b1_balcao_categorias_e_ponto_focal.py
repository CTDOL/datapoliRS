"""Adiciona categorias orgânicas e liderança ponto-focal em tb_atendimentos

Revision ID: z6d7e8f9a0b1
Revises: y5c6d7e8f9a0
Create Date: 2026-11-14 09:47:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'z6d7e8f9a0b1'
down_revision: Union[str, Sequence[str], None] = 'y5c6d7e8f9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tb_balcao_categorias (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            nome TEXT NOT NULL,
            slug TEXT NOT NULL,
            palavras_chave_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            criada_por_ia BOOLEAN NOT NULL DEFAULT FALSE,
            uso_count INTEGER NOT NULL DEFAULT 1,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_balcao_categorias_tenant_slug UNIQUE (tenant_id, slug)
        )
        """
    )
    op.execute(
        "ALTER TABLE tb_atendimentos "
        "ADD COLUMN IF NOT EXISTS lideranca_ponto_focal_id UUID NULL "
        "REFERENCES tb_gabinete_liderancas(id_lideranca) ON DELETE SET NULL"
    )
    op.execute(
        "ALTER TABLE tb_atendimentos "
        "ADD COLUMN IF NOT EXISTS categoria_id UUID NULL "
        "REFERENCES tb_balcao_categorias(id) ON DELETE SET NULL"
    )
    op.execute("ALTER TABLE tb_atendimentos ADD COLUMN IF NOT EXISTS intencao TEXT NULL")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_atendimentos_ponto_focal "
        "ON tb_atendimentos (tenant_id, lideranca_ponto_focal_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_atendimentos_categoria "
        "ON tb_atendimentos (tenant_id, categoria_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_atendimentos_categoria")
    op.execute("DROP INDEX IF EXISTS ix_atendimentos_ponto_focal")
    op.execute("ALTER TABLE tb_atendimentos DROP COLUMN IF EXISTS intencao")
    op.execute("ALTER TABLE tb_atendimentos DROP COLUMN IF EXISTS categoria_id")
    op.execute("ALTER TABLE tb_atendimentos DROP COLUMN IF EXISTS lideranca_ponto_focal_id")
    op.execute("DROP TABLE IF EXISTS tb_balcao_categorias")
