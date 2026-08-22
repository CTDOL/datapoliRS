"""baseline schema

Revision ID: a099af5414b9
Revises: 
Create Date: 2026-08-22 18:52:58.122922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a099af5414b9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Espelha sql/01_init_schema.sql. Idempotente (IF NOT EXISTS em tudo) —
    seguro tanto num banco já inicializado pelo script raw quanto num banco
    totalmente novo, para que este seja o baseline versionado a partir de agora."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "postgis"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "unaccent"')

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_eleicoes (
            cd_eleicao VARCHAR(20) PRIMARY KEY,
            ano_eleicao INT NOT NULL,
            nr_turno INT NOT NULL DEFAULT 1,
            tp_abrangencia VARCHAR(10) NOT NULL,
            ds_eleicao VARCHAR(150) NOT NULL,
            dt_eleicao DATE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_eleicoes_ano ON tb_eleicoes(ano_eleicao)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_municipios (
            cd_ibge_7 VARCHAR(7) PRIMARY KEY,
            cd_tse VARCHAR(10) UNIQUE,
            nm_municipio VARCHAR(150) NOT NULL,
            sg_uf CHAR(2) NOT NULL DEFAULT 'RS',
            geometria GEOMETRY(MultiPolygon, 4326),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_municipios_geom ON tb_municipios USING GIST(geometria)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_municipios_nome ON tb_municipios(nm_municipio)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_municipios_tse ON tb_municipios(cd_tse)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_partidos (
            nr_partido INT PRIMARY KEY,
            sg_partido VARCHAR(20) NOT NULL,
            nm_partido VARCHAR(150) NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_partidos_sigla ON tb_partidos(sg_partido)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_cargos (
            cd_cargo INT PRIMARY KEY,
            ds_cargo VARCHAR(100) NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_candidaturas (
            sq_candidato BIGINT PRIMARY KEY,
            id_tse BIGINT,
            cd_eleicao VARCHAR(20) NOT NULL REFERENCES tb_eleicoes(cd_eleicao),
            cd_cargo INT NOT NULL REFERENCES tb_cargos(cd_cargo),
            nr_candidato INT NOT NULL,
            nm_candidato VARCHAR(255) NOT NULL,
            nm_urna_candidato VARCHAR(150) NOT NULL,
            nr_partido INT NOT NULL REFERENCES tb_partidos(nr_partido),
            sg_uf CHAR(2) NOT NULL DEFAULT 'RS',
            ds_situacao_candidatura VARCHAR(50),
            ds_detalhe_situacao VARCHAR(100),
            st_reeleicao BOOLEAN DEFAULT FALSE,
            vl_total_bens NUMERIC(15, 2) DEFAULT 0.00,
            foto_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_cand_numero_eleicao ON tb_candidaturas(nr_candidato, cd_eleicao)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cand_nome_urna ON tb_candidaturas(nm_urna_candidato)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cand_partido ON tb_candidaturas(nr_partido)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_bens_candidatos (
            id_bem UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            sq_candidato BIGINT NOT NULL REFERENCES tb_candidaturas(sq_candidato) ON DELETE CASCADE,
            ds_tipo_bem VARCHAR(150),
            ds_detalhe_bem TEXT,
            vl_declarado NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_bens_sq_candidato ON tb_bens_candidatos(sq_candidato)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_fato_votacao_munzona (
            id_fato BIGSERIAL PRIMARY KEY,
            cd_eleicao VARCHAR(20) NOT NULL REFERENCES tb_eleicoes(cd_eleicao),
            sq_candidato BIGINT NOT NULL REFERENCES tb_candidaturas(sq_candidato),
            cd_tse_municipio VARCHAR(10) NOT NULL,
            cd_ibge_7 VARCHAR(7) REFERENCES tb_municipios(cd_ibge_7),
            nr_zona INT NOT NULL,
            qt_votos_nominais INT NOT NULL DEFAULT 0,
            qt_votos_validos INT NOT NULL DEFAULT 0,
            CONSTRAINT unq_eleicao_cand_mun_zona UNIQUE (cd_eleicao, sq_candidato, cd_tse_municipio, nr_zona)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_fato_cand_mun ON tb_fato_votacao_munzona(sq_candidato, cd_tse_municipio)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_fato_ibge ON tb_fato_votacao_munzona(cd_ibge_7)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_gabinete_liderancas (
            id_lideranca UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL,
            cd_ibge_7 VARCHAR(7) REFERENCES tb_municipios(cd_ibge_7),
            nm_completo VARCHAR(255) NOT NULL,
            nr_telefone VARCHAR(30),
            ds_email VARCHAR(255),
            tp_influencia VARCHAR(50),
            ds_observacoes TEXT,
            is_ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_liderancas_tenant ON tb_gabinete_liderancas(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_liderancas_municipio ON tb_gabinete_liderancas(cd_ibge_7)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON tb_users(email)")


def downgrade() -> None:
    """Baseline: representa o estado inicial do banco. Sem downgrade —
    reverter significaria apagar todo o schema e os dados eleitorais."""
    raise NotImplementedError("A revisão baseline não suporta downgrade.")
