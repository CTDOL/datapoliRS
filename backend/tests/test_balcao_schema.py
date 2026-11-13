"""[BAL-01] Schema do Balcão Inteligente (Issue #38, ADR 048, DOC_013 §3).

Verifica a migração das sete tabelas do domínio: existência, tenant_id obrigatório com FK
para tb_tenants(id_tenant), CHECKs de domínio fechado, protocolo único por gabinete, FK composta
(tenant_id, id) que impede referência cruzada entre gabinetes e timeline append-only.

Cada teste roda numa transação revertida ao final: não deixa resíduo no banco.
"""
import asyncio
import uuid
from contextlib import asynccontextmanager

import asyncpg
import pytest
from app.core.config import settings

TABELAS = [
    "tb_balcao_portais",
    "tb_balcao_entradas",
    "tb_atendidos",
    "tb_atendimentos",
    "tb_balcao_anexos",
    "tb_balcao_sugestoes",
    "tb_balcao_resolucoes",
]


@asynccontextmanager
async def transacaoRevertida():
    connection = await asyncpg.connect(dsn=settings.DATABASE_URL)
    transacao = connection.transaction()
    await transacao.start()
    try:
        yield connection
    finally:
        await transacao.rollback()
        await connection.close()


async def criarGabinete(connection) -> uuid.UUID:
    return await connection.fetchval(
        "INSERT INTO tb_tenants (nm_mandato, ds_cargo_mandato) VALUES ($1, 'Teste') RETURNING id_tenant",
        f"Gabinete {uuid.uuid4().hex[:8]}",
    )


async def criarAtendido(connection, tenantId, nome="Maria") -> uuid.UUID:
    return await connection.fetchval(
        "INSERT INTO tb_atendidos (tenant_id, nome) VALUES ($1, $2) RETURNING id", tenantId, nome
    )


async def criarPortal(connection, tenantId, tokenHash=None) -> uuid.UUID:
    return await connection.fetchval(
        "INSERT INTO tb_balcao_portais (tenant_id, token_hash) VALUES ($1, $2) RETURNING id",
        tenantId, tokenHash or uuid.uuid4().hex,
    )


async def criarAtendimento(connection, tenantId, atendidoId, protocolo="BAL-2026-000001"):
    return await connection.fetchval(
        """INSERT INTO tb_atendimentos (tenant_id, atendido_id, protocolo, tipo_evento, resumo)
           VALUES ($1, $2, $3, 'CONTATO', 'Pedido de apoio') RETURNING id""",
        tenantId, atendidoId, protocolo,
    )


def rodar(coro):
    return asyncio.run(coro)


def test_sete_tabelas_existem():
    async def _t():
        async with transacaoRevertida() as c:
            existentes = {r["tablename"] for r in await c.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = ANY($1)", TABELAS)}
            assert existentes == set(TABELAS)
    rodar(_t())


def test_toda_tabela_tem_tenant_id_obrigatorio_com_fk_para_tenants():
    async def _t():
        async with transacaoRevertida() as c:
            for tabela in TABELAS:
                coluna = await c.fetchrow(
                    "SELECT data_type, is_nullable FROM information_schema.columns "
                    "WHERE table_name = $1 AND column_name = 'tenant_id'", tabela)
                assert coluna is not None, f"{tabela} sem tenant_id"
                assert coluna["data_type"] == "uuid" and coluna["is_nullable"] == "NO", tabela
                fk = await c.fetchval(
                    """SELECT count(*) FROM pg_constraint
                       WHERE conrelid = $1::regclass AND contype = 'f'
                         AND confrelid = 'tb_tenants'::regclass""", tabela)
                assert fk >= 1, f"{tabela} sem FK para tb_tenants"
    rodar(_t())


def test_status_da_entrada_recusa_valor_fora_do_dominio():
    async def _t():
        async with transacaoRevertida() as c:
            tenant = await criarGabinete(c)
            portal = await criarPortal(c, tenant)
            with pytest.raises(asyncpg.CheckViolationError):
                await c.execute(
                    """INSERT INTO tb_balcao_entradas (tenant_id, portal_id, texto_original, sha256_texto, status)
                       VALUES ($1, $2, 'texto', repeat('a', 64), 'QUALQUER')""", tenant, portal)
    rodar(_t())


def test_entrada_nasce_pendente_com_json_vazio():
    async def _t():
        async with transacaoRevertida() as c:
            tenant = await criarGabinete(c)
            portal = await criarPortal(c, tenant)
            linha = await c.fetchrow(
                """INSERT INTO tb_balcao_entradas (tenant_id, portal_id, texto_original, sha256_texto)
                   VALUES ($1, $2, 'Preciso de ajuda', repeat('b', 64)) RETURNING status, dados_extraidos_json""",
                tenant, portal)
            assert linha["status"] == "PENDENTE"
            assert linha["dados_extraidos_json"] in ("{}", {})
    rodar(_t())


def test_token_hash_do_portal_e_unico_globalmente():
    async def _t():
        async with transacaoRevertida() as c:
            tenantA, tenantB = await criarGabinete(c), await criarGabinete(c)
            await criarPortal(c, tenantA, "hash-repetido")
            with pytest.raises(asyncpg.UniqueViolationError):
                await criarPortal(c, tenantB, "hash-repetido")
    rodar(_t())


def test_protocolo_tem_formato_fixo_e_e_unico_por_gabinete():
    async def _t():
        async with transacaoRevertida() as c:
            tenantA, tenantB = await criarGabinete(c), await criarGabinete(c)
            atendidoA, atendidoB = await criarAtendido(c, tenantA), await criarAtendido(c, tenantB)
            await criarAtendimento(c, tenantA, atendidoA)
            # mesmo protocolo em outro gabinete é permitido
            await criarAtendimento(c, tenantB, atendidoB)
            with pytest.raises(asyncpg.UniqueViolationError):
                async with c.transaction():
                    await criarAtendimento(c, tenantA, atendidoA)
            with pytest.raises(asyncpg.CheckViolationError):
                async with c.transaction():
                    await criarAtendimento(c, tenantA, atendidoA, protocolo="BAL-26-1")
    rodar(_t())


def test_atendimento_nao_referencia_atendido_de_outro_gabinete():
    async def _t():
        async with transacaoRevertida() as c:
            tenantA, tenantB = await criarGabinete(c), await criarGabinete(c)
            atendidoDoB = await criarAtendido(c, tenantB)
            with pytest.raises(asyncpg.ForeignKeyViolationError):
                await criarAtendimento(c, tenantA, atendidoDoB)
    rodar(_t())


def test_entrada_nao_referencia_portal_de_outro_gabinete():
    async def _t():
        async with transacaoRevertida() as c:
            tenantA, tenantB = await criarGabinete(c), await criarGabinete(c)
            portalDoB = await criarPortal(c, tenantB)
            with pytest.raises(asyncpg.ForeignKeyViolationError):
                await c.execute(
                    """INSERT INTO tb_balcao_entradas (tenant_id, portal_id, texto_original, sha256_texto)
                       VALUES ($1, $2, 'x', repeat('c', 64))""", tenantA, portalDoB)
    rodar(_t())


def test_timeline_e_append_only():
    async def _t():
        async with transacaoRevertida() as c:
            tenant = await criarGabinete(c)
            atendimento = await criarAtendimento(c, tenant, await criarAtendido(c, tenant))
            with pytest.raises(asyncpg.PostgresError, match="append-only"):
                async with c.transaction():
                    await c.execute("UPDATE tb_atendimentos SET resumo = 'adulterado' WHERE id = $1", atendimento)
            with pytest.raises(asyncpg.PostgresError, match="append-only"):
                async with c.transaction():
                    await c.execute("DELETE FROM tb_atendimentos WHERE id = $1", atendimento)
            assert await c.fetchval("SELECT resumo FROM tb_atendimentos WHERE id = $1", atendimento) == "Pedido de apoio"
    rodar(_t())


def test_pg_trgm_ativo_com_indice_gin_no_texto_da_entrada():
    async def _t():
        async with transacaoRevertida() as c:
            assert await c.fetchval("SELECT count(*) FROM pg_extension WHERE extname = 'pg_trgm'") == 1
            similaridade = await c.fetchval(
                "SELECT similarity('transporte escolar em Santa Maria', 'transporte escolar Santa Maria')")
            assert similaridade > 0.6
            indice = await c.fetchval(
                """SELECT indexdef FROM pg_indexes
                   WHERE tablename = 'tb_balcao_entradas' AND indexdef ILIKE '%gin%gin_trgm_ops%'""")
            assert indice is not None
    rodar(_t())


def test_atendido_cpf_hash_unico_por_gabinete_e_opcional():
    async def _t():
        async with transacaoRevertida() as c:
            tenantA, tenantB = await criarGabinete(c), await criarGabinete(c)
            await c.execute("INSERT INTO tb_atendidos (tenant_id, nome, cpf_hash) VALUES ($1, 'A', $2)", tenantA, "h1")
            await c.execute("INSERT INTO tb_atendidos (tenant_id, nome, cpf_hash) VALUES ($1, 'B', $2)", tenantB, "h1")
            # sem CPF informado, vários atendidos coexistem
            await c.execute("INSERT INTO tb_atendidos (tenant_id, nome) VALUES ($1, 'C')", tenantA)
            await c.execute("INSERT INTO tb_atendidos (tenant_id, nome) VALUES ($1, 'D')", tenantA)
            with pytest.raises(asyncpg.UniqueViolationError):
                await c.execute("INSERT INTO tb_atendidos (tenant_id, nome, cpf_hash) VALUES ($1, 'E', $2)", tenantA, "h1")
    rodar(_t())
