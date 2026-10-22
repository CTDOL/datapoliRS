"""tb_carga_etl: histórico imutável das cargas do ETL eleitoral

Revision ID: c7d1e2f3a4b5
Revises: a1c3e5f7b9d2
Create Date: 2026-10-22 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c7d1e2f3a4b5'
down_revision: Union[str, Sequence[str], None] = 'a1c3e5f7b9d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Registro somente de inserção de cada carga do ETL (votação e comparecimento).

    Expand-only: tabela nova, sem alterar nenhuma tabela existente. Um CSV traz
    mais de um pleito (ex.: 1º e 2º turnos), por isso cd_eleicoes é uma lista."""
    op.execute("""
        CREATE TABLE tb_carga_etl (
            id_carga BIGSERIAL PRIMARY KEY,
            tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('votacao', 'comparecimento')),
            ano_eleicao INTEGER NOT NULL,
            cd_eleicoes TEXT[] NOT NULL,
            arquivo_origem TEXT NOT NULL,
            sha256 CHAR(64) NOT NULL,
            tamanho_bytes BIGINT NOT NULL,
            iniciado_em TIMESTAMPTZ NOT NULL,
            concluido_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            status VARCHAR(10) NOT NULL CHECK (status IN ('sucesso', 'falha')),
            linhas_carregadas BIGINT,
            erro TEXT,
            operador VARCHAR(100) NOT NULL DEFAULT 'cli'
        );
    """)
    op.execute("""
        CREATE INDEX ix_tb_carga_etl_tipo_ano_concluido
            ON tb_carga_etl (tipo, ano_eleicao, concluido_em DESC);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tb_carga_etl_tipo_ano_concluido;")
    op.execute("DROP TABLE IF EXISTS tb_carga_etl;")
