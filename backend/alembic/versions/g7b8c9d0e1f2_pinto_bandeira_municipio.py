"""tb_municipios: inclui Pinto Bandeira (IBGE 4314548, TSE 89540), ausente da malha local

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-10-22 16:30:00.000000

"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'g7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fonte: API oficial do IBGE (localidades: código 4314548; malhas v3, qualidade intermediária).
# Pinto Bandeira não existe em backend/app/static/rs_municipios.json, por isso entra aqui.
CD_IBGE = "4314548"
CD_TSE = "89540"
NOME = "Pinto Bandeira"
GEOJSON = json.loads('''{"type":"Polygon","coordinates":[[[-51.504,-29.0818],[-51.4973,-29.0875],[-51.5014,-29.1028],[-51.4974,-29.107],[-51.5114,-29.1221],[-51.4866,-29.1222],[-51.479,-29.128],[-51.4752,-29.1382],[-51.4805,-29.1454],[-51.4582,-29.1687],[-51.4233,-29.165],[-51.4232,-29.1562],[-51.4232,-29.1272],[-51.4116,-29.1273],[-51.4129,-29.0875],[-51.4257,-29.0877],[-51.4268,-29.07],[-51.4221,-29.0598],[-51.433,-29.0634],[-51.4409,-29.0594],[-51.4502,-29.0382],[-51.4658,-29.0165],[-51.477,-29.0187],[-51.4817,-29.0295],[-51.4917,-29.0325],[-51.5122,-29.0247],[-51.5218,-29.033],[-51.5208,-29.0433],[-51.4985,-29.0539],[-51.5016,-29.0782],[-51.504,-29.0818]]]}''')


def upgrade() -> None:
    """Idempotente: só insere se o código IBGE ainda não existir."""
    op.get_bind().execute(
        sa.text("""
            INSERT INTO tb_municipios (cd_ibge_7, cd_tse, nm_municipio, sg_uf, geometria)
            VALUES (:cd_ibge, :cd_tse, :nome, 'RS',
                    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)))
            ON CONFLICT (cd_ibge_7) DO NOTHING;
        """),
        {"cd_ibge": CD_IBGE, "cd_tse": CD_TSE, "nome": NOME, "geom": json.dumps(GEOJSON)},
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("DELETE FROM tb_municipios WHERE cd_ibge_7 = :cd_ibge AND cd_tse = :cd_tse;"),
        {"cd_ibge": CD_IBGE, "cd_tse": CD_TSE},
    )
