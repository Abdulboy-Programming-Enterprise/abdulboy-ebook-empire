"""Add gamification tables (badges, achievements, user_badges, user_achievements)

Revision ID: 002_add_gamification
Revises: 001_initial
Create Date: 2026-04-24 11:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '002_add_gamification'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create badges table
    op.create_table('badges',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('criteria_type', sa.String(50), nullable=False),
        sa.Column('criteria_value', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('rarity', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_badges_name'), 'badges', ['name'], unique=True)
    op.create_index(op.f('ix_badges_slug'), 'badges', ['slug'], unique=True)

    # Create user_badges table
    op.create_table('user_badges',
        sa.Column('user_id', UUID(), nullable=False),
        sa.Column('badge_id', UUID(), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'badge_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'], ondelete='CASCADE')
    )

    # Create achievements table
    op.create_table('achievements',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('target_value', sa.Integer(), nullable=False),
        sa.Column('points_awarded', sa.Integer(), nullable=True),
        sa.Column('badge_id', UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['badge_id'], ['badges.id'])
    )
    op.create_index(op.f('ix_achievements_name'), 'achievements', ['name'], unique=True)
    op.create_index(op.f('ix_achievements_slug'), 'achievements', ['slug'], unique=True)

    # Create user_achievements table
    op.create_table('user_achievements',
        sa.Column('user_id', UUID(), nullable=False),
        sa.Column('achievement_id', UUID(), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'achievement_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ondelete='CASCADE')
    )

    # Insert initial badges
    op.execute("""
        INSERT INTO badges (id, name, slug, description, image_url, criteria_type, criteria_value, points, rarity, is_active, created_at, updated_at)
        VALUES 
        (gen_random_uuid(), 'First Chapter', 'first-chapter', 'Read your first book on the platform', '/images/badges/reader_100.svg', 'books_read', 1, 50, 'common', true, NOW(), NOW()),
        (gen_random_uuid(), 'Bookworm', 'bookworm', 'Read 10 books on the platform', '/images/badges/reader_100.svg', 'books_read', 10, 200, 'common', true, NOW(), NOW()),
        (gen_random_uuid(), 'Voracious Reader', 'voracious-reader', 'Read 50 books on the platform', '/images/badges/reviewer_50.svg', 'books_read', 50, 500, 'rare', true, NOW(), NOW()),
        (gen_random_uuid(), 'First Review', 'first-review', 'Write your first book review', '/images/badges/reviewer_50.svg', 'reviews_written', 1, 50, 'common', true, NOW(), NOW()),
        (gen_random_uuid(), 'Helpful Reviewer', 'helpful-reviewer', 'Write 25 book reviews', '/images/badges/reviewer_50.svg', 'reviews_written', 25, 500, 'rare', true, NOW(), NOW()),
        (gen_random_uuid(), 'First Purchase', 'first-purchase', 'Make your first book purchase', '/images/badges/reader_100.svg', 'purchase_count', 1, 50, 'common', true, NOW(), NOW()),
        (gen_random_uuid(), 'Consistent Reader', 'consistent-reader', 'Maintain a 7-day reading streak', '/images/badges/champion.svg', 'streak_days', 7, 100, 'common', true, NOW(), NOW()),
        (gen_random_uuid(), 'Dedicated Reader', 'dedicated-reader', 'Maintain a 30-day reading streak', '/images/badges/champion.svg', 'streak_days', 30, 500, 'rare', true, NOW(), NOW()),
        (gen_random_uuid(), 'Point Gatherer', 'point-gatherer', 'Earn 1,000 total points', '/images/badges/author_10.svg', 'total_points', 1000, 0, 'common', true, NOW(), NOW()),
        (gen_random_uuid(), 'Champion', 'champion', 'Complete all major achievements', '/images/badges/champion.svg', 'special', 0, 1000, 'legendary', true, NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_table('user_achievements')
    op.drop_table('achievements')
    op.drop_table('user_badges')
    op.drop_table('badges')
