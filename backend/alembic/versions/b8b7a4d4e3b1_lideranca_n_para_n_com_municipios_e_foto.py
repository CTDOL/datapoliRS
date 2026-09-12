"""lideranca N para N com municipios e foto

Revision ID: b8b7a4d4e3b1
Revises: 9c52b0a5679c
Create Date: 2026-09-12 03:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8b7a4d4e3b1'
down_revision: Union[str, Sequence[str], None] = '9c52b0a5679c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Uma liderança pode atuar em vários municípios (e um município ter várias
    lideranças) — substitui a FK única cd_ibge_7 por uma tabela de junção N:N.
    Também adiciona ds_foto_url para o upload de foto da liderança.
    """
    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_gabinete_lideranca_municipios (
            id_lideranca UUID NOT NULL REFERENCES tb_gabinete_liderancas(id_lideranca) ON DELETE CASCADE,
            cd_ibge_7 VARCHAR(7) NOT NULL REFERENCES tb_municipios(cd_ibge_7),
            PRIMARY KEY (id_lideranca, cd_ibge_7)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_lideranca_municipios_cd_ibge_7
        ON tb_gabinete_lideranca_municipios(cd_ibge_7);
    """)

    # Backfill: migra o cd_ibge_7 unico ja cadastrado para a tabela de juncao
    # antes de remover a coluna, para nao perder o municipio de nenhum
    # registro existente.
    op.execute("""
        INSERT INTO tb_gabinete_lideranca_municipios (id_lideranca, cd_ibge_7)
        SELECT id_lideranca, cd_ibge_7
        FROM tb_gabinete_liderancas
        WHERE cd_ibge_7 IS NOT NULL
        ON CONFLICT DO NOTHING;
    """)

    op.execute("""
        ALTER TABLE tb_gabinete_liderancas DROP COLUMN IF EXISTS cd_ibge_7;
    """)
    op.execute("""
        ALTER TABLE tb_gabinete_liderancas
        ADD COLUMN IF NOT EXISTS ds_foto_url VARCHAR(500);
    """)


def downgrade() -> None:
    """Reverte para cd_ibge_7 unico (mantem apenas o primeiro municipio de cada liderança, se houver mais de um)."""
    op.execute("""
        ALTER TABLE tb_gabinete_liderancas
        ADD COLUMN IF NOT EXISTS cd_ibge_7 VARCHAR(7) REFERENCES tb_municipios(cd_ibge_7);
    """)
    op.execute("""
        UPDATE tb_gabinete_liderancas l
        SET cd_ibge_7 = (
            SELECT lm.cd_ibge_7 FROM tb_gabinete_lideranca_municipios lm
            WHERE lm.id_lideranca = l.id_lideranca
            ORDER BY lm.cd_ibge_7 LIMIT 1
        );
    """)
    op.execute("ALTER TABLE tb_gabinete_liderancas DROP COLUMN IF EXISTS ds_foto_url;")
    op.execute("DROP TABLE IF EXISTS tb_gabinete_lideranca_municipios;")
