"""merge multiple heads

Revision ID: 87a0289e43c5
Revises: 20250127_add_environment_sound_project_fields, 20250813_add_book_id
Create Date: 2025-08-14 13:32:40.541582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87a0289e43c5'
down_revision = ('20250127_add_environment_sound_project_fields', '20250813_add_book_id')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 