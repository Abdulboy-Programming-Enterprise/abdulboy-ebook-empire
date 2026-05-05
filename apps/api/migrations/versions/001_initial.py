"""Initial migration with all core tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-04-24 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('account_type', sa.String(20), nullable=False),
        sa.Column('theme', sa.String(20), nullable=True),
        sa.Column('text_size', sa.Integer(), nullable=True),
        sa.Column('email_notifications', sa.Boolean(), nullable=True),
        sa.Column('push_notifications', sa.Boolean(), nullable=True),
        sa.Column('total_points', sa.Integer(), nullable=True),
        sa.Column('reading_streak', sa.Integer(), nullable=True),
        sa.Column('last_active_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_status', sa.String(20), nullable=True),
        sa.Column('subscription_started_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_ends_at', sa.DateTime(), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create books table
    op.create_table('books',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('slug', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author_name', sa.String(255), nullable=False),
        sa.Column('author_id', UUID(), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('is_free', sa.Boolean(), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=False),
        sa.Column('preview_pages', sa.Integer(), nullable=True),
        sa.Column('preview_content', sa.Text(), nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('epub_url', sa.String(500), nullable=True),
        sa.Column('cover_image_url', sa.String(500), nullable=True),
        sa.Column('isbn', sa.String(20), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('publication_date', sa.DateTime(), nullable=True),
        sa.Column('enable_watermark', sa.Boolean(), nullable=True),
        sa.Column('watermark_text', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('downloads_count', sa.Integer(), nullable=True),
        sa.Column('views_count', sa.Integer(), nullable=True),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_books_slug'), 'books', ['slug'], unique=True)

    # Create subscription_plans table
    op.create_table('subscription_plans',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('slug', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('features', sa.Text(), nullable=True),
        sa.Column('books_per_month', sa.Integer(), nullable=True),
        sa.Column('download_limit', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscription_plans_slug'), 'subscription_plans', ['slug'], unique=True)

    # Create tags table
    op.create_table('tags',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)
    op.create_index(op.f('ix_tags_slug'), 'tags', ['slug'], unique=True)

    # Create payments table
    op.create_table('payments',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('user_id', UUID(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('item_type', sa.String(20), nullable=False),
        sa.Column('item_id', UUID(), nullable=False),
        sa.Column('gateway_transaction_id', sa.String(255), nullable=True),
        sa.Column('gateway_reference', sa.String(255), nullable=True),
        sa.Column('gateway_response', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('refunded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Create user_subscriptions table
    op.create_table('user_subscriptions',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('user_id', UUID(), nullable=False),
        sa.Column('plan_id', UUID(), nullable=False),
        sa.Column('payment_id', UUID(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('auto_renew', sa.Boolean(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id']),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'])
    )

    # Create user_book_purchases table
    op.create_table('user_book_purchases',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('user_id', UUID(), nullable=False),
        sa.Column('book_id', UUID(), nullable=False),
        sa.Column('payment_id', UUID(), nullable=True),
        sa.Column('purchase_price', sa.Float(), nullable=True),
        sa.Column('purchased_at', sa.DateTime(), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'])
    )
    op.create_unique_constraint('uq_user_book', 'user_book_purchases', ['user_id', 'book_id'])

    # Create bookings table
    op.create_table('bookings',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('user_id', UUID(), nullable=False),
        sa.Column('payment_id', UUID(), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('genre', sa.String(100), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('budget', sa.Float(), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('attachments', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('delivery_url', sa.String(500), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'])
    )

    # Create book_tags association table
    op.create_table('book_tags',
        sa.Column('book_id', UUID(), nullable=False),
        sa.Column('tag_id', UUID(), nullable=False),
        sa.Column('id', UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('book_id', 'tag_id'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE')
    )

    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('user_id', UUID(), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('admin_id', UUID(), nullable=True),
        sa.Column('admin_email', sa.String(255), nullable=True),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('target_type', sa.String(100), nullable=True),
        sa.Column('target_id', UUID(), nullable=True),
        sa.Column('old_values', JSONB(), nullable=True),
        sa.Column('new_values', JSONB(), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL')
    )

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

    # Create analytics_events table
    op.create_table('analytics_events',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('user_id', UUID(), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', JSONB(), nullable=True),
        sa.Column('session_id', UUID(), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )


def downgrade() -> None:
    op.drop_table('analytics_events')
    op.drop_table('user_achievements')
    op.drop_table('achievements')
    op.drop_table('user_badges')
    op.drop_table('badges')
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('book_tags')
    op.drop_table('bookings')
    op.drop_table('user_book_purchases')
    op.drop_table('user_subscriptions')
    op.drop_table('payments')
    op.drop_table('tags')
    op.drop_table('subscription_plans')
    op.drop_table('books')
    op.drop_table('users')
