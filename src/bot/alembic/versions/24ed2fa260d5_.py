"""empty message

Revision ID: 24ed2fa260d5
Revises: 7ccb4b8c807d
Create Date: 2026-05-12 15:59:13.867876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24ed2fa260d5'
down_revision: Union[str, Sequence[str], None] = '7ccb4b8c807d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("""
        WITH ranked AS (
            SELECT id,
                ROW_NUMBER() OVER (
                    PARTITION BY author_id, thread_id, challenge_id
                    ORDER BY id DESC
                ) AS rn
            FROM monthly_submissions
        )
        DELETE FROM monthly_submissions
        WHERE id IN (SELECT id FROM ranked WHERE rn > 1)
    """)
    op.create_unique_constraint(
        'uq_monthly_submissions_challenge_author_thread',
        'monthly_submissions',
        ['challenge_id', 'author_id', 'thread_id']
    )

def downgrade() -> None:
    op.drop_constraint(
        'uq_monthly_submissions_challenge_author_thread',
        'monthly_submissions',
        type_='unique'
    )
