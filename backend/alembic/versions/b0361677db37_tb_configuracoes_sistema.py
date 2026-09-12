"""tb_configuracoes_sistema

Revision ID: b0361677db37
Revises: ae5bbe065aec
Create Date: 2026-08-24 00:37:46.091381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0361677db37'
down_revision: Union[str, Sequence[str], None] = 'ae5bbe065aec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Configurações globais da instância, editáveis em runtime pela tela de
    administração (ciclo eleitoral, rate limiting, TTL de cache) — sem precisar
    reiniciar o processo ou editar .env. As sementes abaixo espelham os valores
    que hoje são constantes fixas em app/core/config.py e nos módulos que usam
    RateLimiter/CacheService, preservando o comportamento atual como padrão."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_configuracoes_sistema (
            chave VARCHAR(80) PRIMARY KEY,
            valor TEXT NOT NULL,
            tipo VARCHAR(20) NOT NULL DEFAULT 'string',
            categoria VARCHAR(30) NOT NULL,
            descricao VARCHAR(255) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    op.execute("""
        INSERT INTO tb_configuracoes_sistema (chave, valor, tipo, categoria, descricao) VALUES
        ('eleitoral.election_year', '2022', 'int', 'eleitoral', 'Ano do pleito usado como padrao quando a busca nao especifica um ano'),
        ('eleitoral.tse_codigo_eleicao', '2040602022', 'string', 'eleitoral', 'Codigo do pleito atribuido pelo TSE, usado na consulta ao DivulgaCandContas'),
        ('eleitoral.default_cargo_code', '7', 'int', 'eleitoral', 'Cargo padrao (cd_cargo) quando a busca nao especifica um cargo'),
        ('rate_limit.login.times', '5', 'int', 'rate_limit', 'Maximo de tentativas de login por janela'),
        ('rate_limit.login.seconds', '60', 'int', 'rate_limit', 'Janela em segundos do limite de tentativas de login'),
        ('rate_limit.trocar_senha.times', '5', 'int', 'rate_limit', 'Maximo de trocas de senha por janela'),
        ('rate_limit.trocar_senha.seconds', '60', 'int', 'rate_limit', 'Janela em segundos do limite de troca de senha'),
        ('rate_limit.cabinet.times', '30', 'int', 'rate_limit', 'Maximo de requisicoes por janela no modulo de Liderancas'),
        ('rate_limit.cabinet.seconds', '1', 'int', 'rate_limit', 'Janela em segundos do limite de Liderancas'),
        ('rate_limit.amendments.times', '30', 'int', 'rate_limit', 'Maximo de requisicoes por janela no modulo de Emendas'),
        ('rate_limit.amendments.seconds', '1', 'int', 'rate_limit', 'Janela em segundos do limite de Emendas'),
        ('rate_limit.legislative.times', '30', 'int', 'rate_limit', 'Maximo de requisicoes por janela no modulo de Projetos de Lei'),
        ('rate_limit.legislative.seconds', '1', 'int', 'rate_limit', 'Janela em segundos do limite de Projetos de Lei'),
        ('rate_limit.geo.times', '30', 'int', 'rate_limit', 'Maximo de requisicoes por janela no modulo Geoespacial'),
        ('rate_limit.geo.seconds', '1', 'int', 'rate_limit', 'Janela em segundos do limite Geoespacial'),
        ('rate_limit.voting.times', '20', 'int', 'rate_limit', 'Maximo de requisicoes por janela no modulo de Votacao e Candidatos'),
        ('rate_limit.voting.seconds', '1', 'int', 'rate_limit', 'Janela em segundos do limite de Votacao e Candidatos'),
        ('rate_limit.tenant.times', '30', 'int', 'rate_limit', 'Maximo de requisicoes por janela no modulo de Configuracoes do Gabinete'),
        ('rate_limit.tenant.seconds', '1', 'int', 'rate_limit', 'Janela em segundos do limite de Configuracoes do Gabinete'),
        ('rate_limit.tasks.times', '30', 'int', 'rate_limit', 'Maximo de requisicoes por janela no modulo de Tarefas'),
        ('rate_limit.tasks.seconds', '1', 'int', 'rate_limit', 'Janela em segundos do limite de Tarefas'),
        ('cache_ttl.candidate_votes', '86400', 'int', 'cache', 'Duracao do cache em segundos da votacao por candidato'),
        ('cache_ttl.cargos', '2592000', 'int', 'cache', 'Duracao do cache em segundos da lista de cargos eleitorais'),
        ('cache_ttl.eleicoes', '3600', 'int', 'cache', 'Duracao do cache em segundos da lista de pleitos disponiveis'),
        ('cache_ttl.geojson_municipios', '604800', 'int', 'cache', 'Duracao do cache em segundos do GeoJSON dos municipios')
        ON CONFLICT (chave) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tb_configuracoes_sistema")
