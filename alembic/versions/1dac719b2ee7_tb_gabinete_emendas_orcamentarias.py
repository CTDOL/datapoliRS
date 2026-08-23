"""tb_gabinete_emendas orcamentarias

Revision ID: 1dac719b2ee7
Revises: ba54000227b6
Create Date: 2026-08-23 08:43:10.527670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dac719b2ee7'
down_revision: Union[str, Sequence[str], None] = 'ba54000227b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria tb_gabinete_emendas: emendas orçamentárias do gabinete, isoladas por tenant."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_gabinete_emendas (
            id_emenda UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant) ON DELETE CASCADE,
            cd_ibge_7 VARCHAR(7) REFERENCES tb_municipios(cd_ibge_7),
            nr_emenda VARCHAR(50),
            ano_exercicio INT NOT NULL,
            tp_emenda VARCHAR(30),
            ds_area VARCHAR(100),
            ds_objeto TEXT NOT NULL,
            vl_indicado NUMERIC(14, 2) NOT NULL DEFAULT 0,
            vl_empenhado NUMERIC(14, 2) NOT NULL DEFAULT 0,
            vl_pago NUMERIC(14, 2) NOT NULL DEFAULT 0,
            tp_situacao VARCHAR(30) NOT NULL DEFAULT 'Indicada',
            ds_observacoes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_emendas_tenant ON tb_gabinete_emendas(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_emendas_municipio ON tb_gabinete_emendas(cd_ibge_7)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_emendas_ano ON tb_gabinete_emendas(ano_exercicio)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_emendas_situacao ON tb_gabinete_emendas(tp_situacao)")


def downgrade() -> None:
    """Remove tb_gabinete_emendas."""
    op.execute("DROP TABLE IF EXISTS tb_gabinete_emendas")
