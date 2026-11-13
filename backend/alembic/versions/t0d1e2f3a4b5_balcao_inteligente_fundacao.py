"""Balcão Inteligente: portais, entradas, atendidos, atendimentos, anexos, sugestões e resoluções

ONDA 2, Fatia 1 (Issue #38, ADR 048, DOC_013 §3). Migração só aditiva: cria sete tabelas e a
extensão pg_trgm, sem tocar em nenhuma tabela existente (Gate de Banco do Modelo 32, Regra 12.2).

Isolamento entre gabinetes no banco: toda tabela tem tenant_id NOT NULL com FK para
tb_tenants(id_tenant), e as referências entre tabelas do Balcão são FKs compostas
(tenant_id, id). Um registro do gabinete A não consegue apontar para um registro do gabinete B,
mesmo que o filtro por tenant_id falte em algum repositório.

tb_atendimentos é a linha do tempo e só aceita INSERT (trigger). Por isso as FKs que a
alcançam não usam ON DELETE SET NULL, que seria um UPDATE.

Revision ID: t0d1e2f3a4b5
Revises: s9c0d1e2f3a4
Create Date: 2026-11-13 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 't0d1e2f3a4b5'
down_revision: Union[str, Sequence[str], None] = 's9c0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELAS_NA_ORDEM_DE_CRIACAO = [
    "tb_balcao_portais",
    "tb_balcao_entradas",
    "tb_atendidos",
    "tb_atendimentos",
    "tb_balcao_anexos",
    "tb_balcao_sugestoes",
    "tb_balcao_resolucoes",
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute("""
        CREATE TABLE tb_balcao_portais (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant),
            token_hash TEXT NOT NULL,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_balcao_portais_token_hash UNIQUE (token_hash),
            CONSTRAINT uq_balcao_portais_tenant_id UNIQUE (tenant_id, id)
        )
    """)

    op.execute("""
        CREATE TABLE tb_balcao_entradas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant),
            portal_id UUID NOT NULL,
            texto_original TEXT NOT NULL,
            sha256_texto CHAR(64) NOT NULL,
            status VARCHAR(12) NOT NULL DEFAULT 'PENDENTE',
            dados_extraidos_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_balcao_entradas_status CHECK (status IN ('PENDENTE', 'EFETIVADA', 'DESCARTADA')),
            CONSTRAINT uq_balcao_entradas_tenant_id UNIQUE (tenant_id, id),
            CONSTRAINT fk_balcao_entradas_portal FOREIGN KEY (tenant_id, portal_id)
                REFERENCES tb_balcao_portais (tenant_id, id)
        )
    """)
    op.execute("CREATE INDEX ix_balcao_entradas_fila ON tb_balcao_entradas (tenant_id, status, criado_em DESC)")
    op.execute("CREATE INDEX ix_balcao_entradas_sha256 ON tb_balcao_entradas (tenant_id, sha256_texto)")
    op.execute("CREATE INDEX ix_balcao_entradas_texto_trgm ON tb_balcao_entradas USING gin (texto_original gin_trgm_ops)")

    op.execute("""
        CREATE TABLE tb_atendidos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant),
            nome VARCHAR(200) NOT NULL,
            cpf_hash TEXT,
            telefone VARCHAR(30),
            email VARCHAR(254),
            municipio_id VARCHAR(7) REFERENCES tb_municipios(cd_ibge_7),
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_atendidos_tenant_id UNIQUE (tenant_id, id)
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_atendidos_cpf_hash ON tb_atendidos (tenant_id, cpf_hash) WHERE cpf_hash IS NOT NULL")
    op.execute("CREATE INDEX ix_atendidos_nome ON tb_atendidos (tenant_id, nome)")

    op.execute("""
        CREATE TABLE tb_atendimentos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant),
            atendido_id UUID NOT NULL,
            protocolo VARCHAR(15) NOT NULL,
            tipo_evento VARCHAR(30) NOT NULL,
            resumo TEXT NOT NULL,
            criado_por_user_id UUID REFERENCES tb_users(id),
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_atendimentos_protocolo CHECK (protocolo ~ '^BAL-[0-9]{4}-[0-9]{6}$'),
            CONSTRAINT uq_atendimentos_protocolo UNIQUE (tenant_id, protocolo),
            CONSTRAINT uq_atendimentos_tenant_id UNIQUE (tenant_id, id),
            CONSTRAINT fk_atendimentos_atendido FOREIGN KEY (tenant_id, atendido_id)
                REFERENCES tb_atendidos (tenant_id, id)
        )
    """)
    op.execute("CREATE INDEX ix_atendimentos_timeline ON tb_atendimentos (tenant_id, atendido_id, criado_em)")
    op.execute("""
        CREATE FUNCTION fn_atendimentos_append_only() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'tb_atendimentos é append-only: correções entram como novo evento';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_atendimentos_append_only
        BEFORE UPDATE OR DELETE ON tb_atendimentos
        FOR EACH ROW EXECUTE FUNCTION fn_atendimentos_append_only()
    """)

    op.execute("""
        CREATE TABLE tb_balcao_anexos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant),
            entrada_id UUID,
            atendimento_id UUID,
            caminho_arquivo TEXT NOT NULL,
            sha256_arquivo CHAR(64) NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            tamanho_bytes BIGINT NOT NULL,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_balcao_anexos_origem CHECK (entrada_id IS NOT NULL OR atendimento_id IS NOT NULL),
            CONSTRAINT ck_balcao_anexos_tamanho CHECK (tamanho_bytes > 0),
            CONSTRAINT uq_balcao_anexos_tenant_id UNIQUE (tenant_id, id),
            CONSTRAINT fk_balcao_anexos_entrada FOREIGN KEY (tenant_id, entrada_id)
                REFERENCES tb_balcao_entradas (tenant_id, id),
            CONSTRAINT fk_balcao_anexos_atendimento FOREIGN KEY (tenant_id, atendimento_id)
                REFERENCES tb_atendimentos (tenant_id, id)
        )
    """)
    op.execute("CREATE INDEX ix_balcao_anexos_entrada ON tb_balcao_anexos (tenant_id, entrada_id)")

    op.execute("""
        CREATE TABLE tb_balcao_sugestoes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant),
            entrada_id UUID NOT NULL,
            entrada_similar_id UUID,
            atendimento_relacionado_id UUID,
            score_similaridade NUMERIC(4,3) NOT NULL,
            motivo VARCHAR(30) NOT NULL,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_balcao_sugestoes_score CHECK (score_similaridade BETWEEN 0 AND 1),
            CONSTRAINT ck_balcao_sugestoes_alvo CHECK (entrada_similar_id IS NOT NULL OR atendimento_relacionado_id IS NOT NULL),
            CONSTRAINT fk_balcao_sugestoes_entrada FOREIGN KEY (tenant_id, entrada_id)
                REFERENCES tb_balcao_entradas (tenant_id, id),
            CONSTRAINT fk_balcao_sugestoes_similar FOREIGN KEY (tenant_id, entrada_similar_id)
                REFERENCES tb_balcao_entradas (tenant_id, id),
            CONSTRAINT fk_balcao_sugestoes_atendimento FOREIGN KEY (tenant_id, atendimento_relacionado_id)
                REFERENCES tb_atendimentos (tenant_id, id)
        )
    """)
    op.execute("CREATE INDEX ix_balcao_sugestoes_entrada ON tb_balcao_sugestoes (tenant_id, entrada_id)")

    op.execute("""
        CREATE TABLE tb_balcao_resolucoes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tb_tenants(id_tenant),
            atendimento_id UUID NOT NULL,
            despacho TEXT NOT NULL,
            evidencia_anexo_id UUID NOT NULL,
            resolvido_por_user_id UUID NOT NULL REFERENCES tb_users(id),
            resolvido_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_balcao_resolucoes_despacho CHECK (length(btrim(despacho)) > 0),
            CONSTRAINT fk_balcao_resolucoes_atendimento FOREIGN KEY (tenant_id, atendimento_id)
                REFERENCES tb_atendimentos (tenant_id, id),
            CONSTRAINT fk_balcao_resolucoes_anexo FOREIGN KEY (tenant_id, evidencia_anexo_id)
                REFERENCES tb_balcao_anexos (tenant_id, id)
        )
    """)
    op.execute("CREATE INDEX ix_balcao_resolucoes_recentes ON tb_balcao_resolucoes (tenant_id, atendimento_id, resolvido_em DESC)")


def downgrade() -> None:
    """Remove as sete tabelas e perde os dados do Balcão. Em produção a reversão exige decisão
    do operador. A extensão pg_trgm fica, porque outra migração pode passar a depender dela."""
    op.execute("DROP TRIGGER IF EXISTS trg_atendimentos_append_only ON tb_atendimentos")
    for tabela in reversed(TABELAS_NA_ORDEM_DE_CRIACAO):
        op.execute(f"DROP TABLE IF EXISTS {tabela}")
    op.execute("DROP FUNCTION IF EXISTS fn_atendimentos_append_only()")
