"""nm_municipio_tse em tb_fato_votacao_munzona

Revision ID: 9c52b0a5679c
Revises: b0361677db37
Create Date: 2026-09-12 03:29:35.269851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c52b0a5679c'
down_revision: Union[str, Sequence[str], None] = 'b0361677db37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Guarda o NM_MUNICIPIO bruto do TSE em tb_fato_votacao_munzona.

    O TSE usa, para alguns registros, um cd_tse_municipio "extra" que nao
    bate com o cd_tse ja cadastrado em tb_municipios para aquela mesma
    cidade (ex.: codigo 88013 = "PORTO ALEGRE" no CSV, mas Porto Alegre ja
    tem outro cd_tse "oficial" cadastrado). Sem esse nome, o JOIN falha e a
    API cai num fallback generico ("Municipio {codigo}"). Guardando o nome
    que o proprio TSE ja informa na linha, o rotulo exibido fica sempre
    correto mesmo quando o JOIN por codigo nao encontra correspondencia.
    """
    op.execute("""
        ALTER TABLE tb_fato_votacao_munzona
        ADD COLUMN IF NOT EXISTS nm_municipio_tse VARCHAR(150);
    """)


def downgrade() -> None:
    """Remove a coluna nm_municipio_tse."""
    op.execute("""
        ALTER TABLE tb_fato_votacao_munzona
        DROP COLUMN IF EXISTS nm_municipio_tse;
    """)
