"""tb_log_acesso: eventos de operações sobre dados pessoais (revisão de 2026-10-24, achado M5)

Amplia o CHECK de evento com exportacao_dados, lideranca_excluida e usuario_alterado.
Expand: só amplia o domínio, os eventos antigos continuam válidos.

Revision ID: s9c0d1e2f3a4
Revises: r8b9c0d1e2f3
Create Date: 2026-10-24 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 's9c0d1e2f3a4'
down_revision: Union[str, Sequence[str], None] = 'r8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CHECK = "ck_log_acesso_evento"
ANTIGOS = "'login_ok', 'login_falha', 'acesso_negado_403'"
NOVOS = "'exportacao_dados', 'lideranca_excluida', 'usuario_alterado'"


def upgrade() -> None:
    op.execute(f"ALTER TABLE tb_log_acesso DROP CONSTRAINT IF EXISTS {CHECK}")
    op.execute(f"ALTER TABLE tb_log_acesso ADD CONSTRAINT {CHECK} CHECK (evento IN ({ANTIGOS}, {NOVOS}))")


def downgrade() -> None:
    """Só é seguro sem registros dos eventos novos: o CHECK antigo recusaria a tabela.
    Os registros novos são apagados antes, o que perde trilha de auditoria. Por isso a
    reversão exige decisão do operador, e não roda em produção por padrão do deploy."""
    op.execute(f"ALTER TABLE tb_log_acesso DROP CONSTRAINT IF EXISTS {CHECK}")
    op.execute(f"DELETE FROM tb_log_acesso WHERE evento IN ({NOVOS})")
    op.execute(f"ALTER TABLE tb_log_acesso ADD CONSTRAINT {CHECK} CHECK (evento IN ({ANTIGOS}))")
