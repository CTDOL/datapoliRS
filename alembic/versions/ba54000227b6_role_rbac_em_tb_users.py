"""role rbac em tb_users

Revision ID: ba54000227b6
Revises: a1961e63fbe4
Create Date: 2026-08-22 19:08:22.505043

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba54000227b6'
down_revision: Union[str, Sequence[str], None] = 'a1961e63fbe4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona controle de papel (RBAC) em tb_users.

    Default 'operador' para não elevar silenciosamente nenhum usuário
    existente — o bootstrap.py força 'admin' explicitamente para o
    usuário administrador em todo startup.
    """
    op.execute("""
        ALTER TABLE tb_users
        ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'operador'
    """)
    op.execute("""
        ALTER TABLE tb_users
        ADD CONSTRAINT ck_users_role CHECK (role IN ('admin', 'operador', 'leitor'))
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tb_users DROP CONSTRAINT IF EXISTS ck_users_role")
    op.execute("ALTER TABLE tb_users DROP COLUMN IF EXISTS role")
