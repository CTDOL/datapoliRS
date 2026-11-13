"""tb_log_acesso: adiciona eventos de auditoria do Balcão Inteligente

Amplia o CHECK ck_log_acesso_evento com balcao_efetivado, balcao_descartado,
balcao_resolvido e balcao_anexo_baixado (Expand: eventos antigos seguem válidos).

Revision ID: u1e2f3a4b5c6
Revises: t0d1e2f3a4b5
Create Date: 2026-11-13 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'u1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 't0d1e2f3a4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CHECK = "ck_log_acesso_evento"
ANTIGOS = (
    "'login_ok', 'login_falha', 'acesso_negado_403', "
    "'exportacao_dados', 'lideranca_excluida', 'usuario_alterado'"
)
NOVOS = "'balcao_efetivado', 'balcao_descartado', 'balcao_resolvido', 'balcao_anexo_baixado'"


def upgrade() -> None:
    op.execute(f"ALTER TABLE tb_log_acesso DROP CONSTRAINT IF EXISTS {CHECK}")
    op.execute(f"ALTER TABLE tb_log_acesso ADD CONSTRAINT {CHECK} CHECK (evento IN ({ANTIGOS}, {NOVOS}))")


def downgrade() -> None:
    op.execute(f"ALTER TABLE tb_log_acesso DROP CONSTRAINT IF EXISTS {CHECK}")
    op.execute(f"DELETE FROM tb_log_acesso WHERE evento IN ({NOVOS})")
    op.execute(f"ALTER TABLE tb_log_acesso ADD CONSTRAINT {CHECK} CHECK (evento IN ({ANTIGOS}))")

