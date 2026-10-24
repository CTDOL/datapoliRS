"""tb_log_acesso: trilha de acesso com expurgo de 6 meses (ADR 040)

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2026-10-23 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'k1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'j0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS tb_log_acesso (
            id BIGSERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            evento VARCHAR(30) NOT NULL,
            email VARCHAR(200) NULL,
            tenant_id UUID NULL,
            caminho VARCHAR(300) NULL,
            ip VARCHAR(64) NULL,
            status_http INTEGER NULL,
            CONSTRAINT ck_log_acesso_evento CHECK (evento IN ('login_ok', 'login_falha', 'acesso_negado_403'))
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_log_acesso_created_at ON tb_log_acesso (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_log_acesso_evento_email ON tb_log_acesso (evento, email)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tb_log_acesso")
