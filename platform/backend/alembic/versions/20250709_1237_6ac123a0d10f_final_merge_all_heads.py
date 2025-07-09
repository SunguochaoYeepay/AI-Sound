"""final_merge_all_heads

Revision ID: 6ac123a0d10f
Revises: add_character_summary_to_books, 7ea68f195f62
Create Date: 2025-07-09 12:37:52.878658

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ac123a0d10f'
down_revision = ('add_character_summary_to_books', '7ea68f195f62')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 