"""tb_municipios: preenche cd_tse de três municípios que estavam sem código TSE

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-10-22 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Código IBGE (cadastro, presente na malha rs_municipios.json) -> código TSE (CSV de votação 2026, CD_MUNICIPIO).
# Os nomes conferem nas duas fontes: Restinga Seca, Sant' Ana do Livramento e Vespasiano Correa.
CODIGOS_TSE = {
    "4315503": "88137",  # Restinga Seca
    "4317103": "88455",  # Sant' Ana do Livramento
    "4322855": "88781",  # Vespasiano Correa
}


def upgrade() -> None:
    """Expand-only e idempotente: só preenche onde cd_tse ainda é nulo, e não sobrescreve código existente."""
    for codigoIbge, codigoTse in CODIGOS_TSE.items():
        op.execute(f"""
            UPDATE tb_municipios
               SET cd_tse = '{codigoTse}'
             WHERE cd_ibge_7 = '{codigoIbge}' AND cd_tse IS NULL;
        """)


def downgrade() -> None:
    """Reverte só os códigos que esta migração preencheu."""
    for codigoIbge, codigoTse in CODIGOS_TSE.items():
        op.execute(f"""
            UPDATE tb_municipios
               SET cd_tse = NULL
             WHERE cd_ibge_7 = '{codigoIbge}' AND cd_tse = '{codigoTse}';
        """)
