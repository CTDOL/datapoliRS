"""Endereços e chaves liga/desliga das APIs externas, editáveis pelo super-admin

Revision ID: l2a3b4c5d6e7
Revises: k1f2a3b4c5d6
Create Date: 2026-10-23 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'l2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'k1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Sementes espelham as constantes atuais dos adaptadores, então o comportamento não muda até o operador editar.
SEMENTES = [
    ('api.tse.base_url', 'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura', 'string', 'Endereço base da API do TSE (DivulgaCandContas)'),
    ('api.tse.ativa', '1', 'int', 'Consulta ao TSE ligada (1) ou desligada (0)'),
    ('api.camara.base_url', 'https://dadosabertos.camara.leg.br/api/v2', 'string', 'Endereço base da API de Dados Abertos da Câmara'),
    ('api.camara.ativa', '1', 'int', 'Busca na Câmara ligada (1) ou desligada (0)'),
    ('api.senado.base_url', 'https://legis.senado.leg.br/dadosabertos', 'string', 'Endereço base da API de Dados Abertos do Senado'),
    ('api.senado.ativa', '1', 'int', 'Busca no Senado ligada (1) ou desligada (0)'),
    ('api.alrs.base_url', 'https://ww4.al.rs.gov.br', 'string', 'Endereço base do portal da Assembleia Legislativa do RS'),
    ('api.alrs.ativa', '1', 'int', 'Busca na ALRS ligada (1) ou desligada (0)'),
]


def upgrade() -> None:
    for chave, valor, tipo, descricao in SEMENTES:
        op.execute(
            "INSERT INTO tb_configuracoes_sistema (chave, valor, tipo, categoria, descricao) "
            f"VALUES ('{chave}', '{valor}', '{tipo}', 'apis', '{descricao}') "
            "ON CONFLICT (chave) DO NOTHING"
        )


def downgrade() -> None:
    chaves = ", ".join(f"'{chave}'" for chave, *_ in SEMENTES)
    op.execute(f"DELETE FROM tb_configuracoes_sistema WHERE chave IN ({chaves})")
