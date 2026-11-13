"""Configurações em runtime do comutador IA/Regex do Balcão Inteligente

Revision ID: v2f3a4b5c6d7
Revises: u1e2f3a4b5c6
Create Date: 2026-11-13 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'v2f3a4b5c6d7'
down_revision: Union[str, Sequence[str], None] = 'u1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEMENTES = [
    ('balcao.ia.provider', '', 'string', 'Motor de extração do Balcão: vazio/regex (determinístico), openai, ollama, gemini ou anthropic'),
    ('balcao.ia.model', '', 'string', 'Modelo LLM usado pelo provedor ativo do Balcão (vazio usa o padrão do provedor)'),
    ('balcao.ia.base_url', '', 'string', 'Base URL opcional para provedor OpenAI-compatível (ex.: Ollama/vLLM)'),
]


def upgrade() -> None:
    for chave, valor, tipo, descricao in SEMENTES:
        op.execute(
            "INSERT INTO tb_configuracoes_sistema (chave, valor, tipo, categoria, descricao) "
            f"VALUES ('{chave}', '{valor}', '{tipo}', 'balcao_ia', '{descricao}') "
            "ON CONFLICT (chave) DO NOTHING"
        )


def downgrade() -> None:
    chaves = ", ".join(f"'{chave}'" for chave, *_ in SEMENTES)
    op.execute(f"DELETE FROM tb_configuracoes_sistema WHERE chave IN ({chaves})")

