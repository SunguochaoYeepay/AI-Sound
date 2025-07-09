"""merge_character_and_environment_heads

Revision ID: 7ea68f195f62
Revises: 20250125_add_environment_sound_id_to_tracks, 20250130_add_book_chapter_v2
Create Date: 2025-07-09 12:34:28.889584

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ea68f195f62'
down_revision = ('20250125_add_environment_sound_id_to_tracks', '20250130_add_book_chapter_v2')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 