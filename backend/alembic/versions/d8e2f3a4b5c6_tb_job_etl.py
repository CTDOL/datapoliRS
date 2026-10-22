"""tb_job_etl: fila de cargas do ETL eleitoral, consumida pelo worker

Revision ID: d8e2f3a4b5c6
Revises: c7d1e2f3a4b5
Create Date: 2026-10-22 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd8e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'c7d1e2f3a4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fila de jobs. O índice único parcial garante que só exista um job ativo por vez."""
    op.execute("""
        CREATE TABLE tb_job_etl (
            id_job BIGSERIAL PRIMARY KEY,
            tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('votacao', 'comparecimento')),
            ano_eleicao INTEGER NOT NULL,
            status VARCHAR(12) NOT NULL CHECK (status IN ('pendente', 'executando', 'concluido', 'falha')),
            solicitado_por VARCHAR(255) NOT NULL,
            solicitado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            iniciado_em TIMESTAMPTZ,
            concluido_em TIMESTAMPTZ,
            erro TEXT
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX ux_tb_job_etl_ativo
            ON tb_job_etl ((1)) WHERE status IN ('pendente', 'executando');
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_tb_job_etl_ativo;")
    op.execute("DROP TABLE IF EXISTS tb_job_etl;")
