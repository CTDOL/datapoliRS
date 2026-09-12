"""tb_fato_comparecimento_munzona eleitorado e comparecimento

Revision ID: 895f8ce12277
Revises: b8b7a4d4e3b1
Create Date: 2026-09-12 01:30:13.990083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '895f8ce12277'
down_revision: Union[str, Sequence[str], None] = 'b8b7a4d4e3b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria tb_fato_comparecimento_munzona: eleitorado apto, comparecimento e
    abstenções por município/zona/eleição, extraído do dataset TSE
    detalhe_votacao_munzona (fonte independente de votacao_candidato_munzona,
    que só carrega votos nominais por candidato)."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_fato_comparecimento_munzona (
            cd_eleicao VARCHAR(20) NOT NULL,
            cd_tse_municipio VARCHAR(10) NOT NULL,
            nr_zona INT NOT NULL,
            nm_municipio_tse VARCHAR(150),
            qt_aptos INT NOT NULL DEFAULT 0,
            qt_comparecimento INT NOT NULL DEFAULT 0,
            qt_abstencoes INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (cd_eleicao, cd_tse_municipio, nr_zona)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_comparecimento_eleicao "
        "ON tb_fato_comparecimento_munzona(cd_eleicao)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_comparecimento_municipio "
        "ON tb_fato_comparecimento_munzona(cd_tse_municipio)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS tb_fato_comparecimento_munzona")
