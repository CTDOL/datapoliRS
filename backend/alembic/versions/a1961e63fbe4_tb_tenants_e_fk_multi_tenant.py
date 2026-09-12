"""tb_tenants e fk multi tenant

Revision ID: a1961e63fbe4
Revises: a099af5414b9
Create Date: 2026-08-22 18:52:58.692725

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1961e63fbe4'
down_revision: Union[str, Sequence[str], None] = 'a099af5414b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria tb_tenants e transforma tenant_id de UUID solto em FK real.

    Backfill dinâmico: qualquer tenant_id já em uso em tb_users ou
    tb_gabinete_liderancas (o admin de bootstrap, dados de teste, etc.)
    ganha uma linha placeholder em tb_tenants antes da FK ser aplicada —
    sem isso, o ALTER TABLE falharia contra dados existentes.
    """
    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_tenants (
            id_tenant UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nm_mandato VARCHAR(150) NOT NULL,
            ds_cargo_mandato VARCHAR(50) NOT NULL,
            nr_partido INT REFERENCES tb_partidos(nr_partido),
            cd_ibge_base VARCHAR(7) REFERENCES tb_municipios(cd_ibge_7),
            is_ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    op.execute("""
        INSERT INTO tb_tenants (id_tenant, nm_mandato, ds_cargo_mandato)
        SELECT DISTINCT tenant_id, 'Gabinete ' || tenant_id::text, 'Não especificado'
        FROM tb_users
        WHERE tenant_id IS NOT NULL
        ON CONFLICT (id_tenant) DO NOTHING
    """)
    op.execute("""
        INSERT INTO tb_tenants (id_tenant, nm_mandato, ds_cargo_mandato)
        SELECT DISTINCT tenant_id, 'Gabinete ' || tenant_id::text, 'Não especificado'
        FROM tb_gabinete_liderancas
        WHERE tenant_id IS NOT NULL
        ON CONFLICT (id_tenant) DO NOTHING
    """)

    op.execute("""
        ALTER TABLE tb_users
        ADD CONSTRAINT fk_user_tenant
        FOREIGN KEY (tenant_id) REFERENCES tb_tenants(id_tenant) ON DELETE RESTRICT
    """)
    op.execute("""
        ALTER TABLE tb_gabinete_liderancas
        ADD CONSTRAINT fk_lideranca_tenant
        FOREIGN KEY (tenant_id) REFERENCES tb_tenants(id_tenant) ON DELETE CASCADE
    """)


def downgrade() -> None:
    """Remove as FKs e a tabela tb_tenants, devolvendo tenant_id a UUID solto."""
    op.execute("ALTER TABLE tb_gabinete_liderancas DROP CONSTRAINT IF EXISTS fk_lideranca_tenant")
    op.execute("ALTER TABLE tb_users DROP CONSTRAINT IF EXISTS fk_user_tenant")
    op.execute("DROP TABLE IF EXISTS tb_tenants")
