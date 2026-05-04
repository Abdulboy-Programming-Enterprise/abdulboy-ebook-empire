#!/usr/bin/env python
# =============================================================================
# ALEMBIC MIGRATION ENVIRONMENT
# =============================================================================
# This file sets up the Alembic environment for database migrations
# =============================================================================

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../apps/api'))

# Import SQLAlchemy models
from app.models.base import Base
from app.models.user import User  # noqa
from app.models.book import Book, Tag, BookTag  # noqa
from app.models.subscription import SubscriptionPlan, UserSubscription  # noqa
from app.models.booking import Booking  # noqa
from app.models.payment import Payment, UserBookPurchase  # noqa
from app.models.analytics import AnalyticsEvent  # noqa
from app.models.suggestion import SuggestionLog  # noqa
from app.models.affiliate import AffiliateLink, AffiliateClick  # noqa
from app.models.notification import Notification  # noqa
from app.models.audit import AuditLog  # noqa
from app.models.badge import Badge, UserBadge  # noqa
from app.models.achievement import Achievement, UserAchievement  # noqa

# =============================================================================
# Alembic Config object
# =============================================================================
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata


def get_database_url():
    """Get database URL from environment or config."""
    # Try to get from environment first
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        return database_url
    
    # Fall back to Alembic config
    return config.get_main_option('sqlalchemy.url')


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            version_table='alembic_version',
            version_table_schema='app',
        )

        with context.begin_transaction():
            context.run_migrations()


# =============================================================================
# Migration Context Functions
# =============================================================================
def include_object(object, name, type_, reflected, compare_to):
    """Filter which objects should be included in migrations."""
    # Skip objects in certain schemas if needed
    if type_ == 'table' and object.schema not in ['app', 'analytics', 'audit']:
        return False
    
    return True


def include_name(name, type_, parent_names):
    """Filter which names should be included in migrations."""
    # Skip internal PostgreSQL objects
    if type_ == 'schema' and name == 'information_schema':
        return False
    if type_ == 'schema' and name.startswith('pg_'):
        return False
    
    return True


def run_migrations():
    """Run migrations in the appropriate mode."""
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


# =============================================================================
# Custom Migration Operations
# =============================================================================
def create_partitioned_table(partition_key='created_at'):
    """Helper to create partitioned tables."""
    from alembic import op
    from sqlalchemy import text
    
    def create_monthly_partitions(table_name, start_date, end_date):
        """Create monthly partitions for a table."""
        current_date = start_date
        while current_date <= end_date:
            partition_name = f"{table_name}_{current_date.strftime('%Y_%m')}"
            next_date = current_date.replace(
                month=current_date.month + 1,
                day=1
            ) if current_date.month < 12 else current_date.replace(
                year=current_date.year + 1,
                month=1,
                day=1
            )
            
            op.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF {table_name}
                FOR VALUES FROM ('{current_date.isoformat()}') TO ('{next_date.isoformat()}')
            """))
            
            current_date = next_date
    
    return create_monthly_partitions


def create_audit_trigger(table_name):
    """Helper to create audit triggers on a table."""
    from alembic import op
    from sqlalchemy import text
    
    trigger_name = f"audit_{table_name}_changes"
    function_name = f"audit_{table_name}_function"
    
    # Create audit function
    op.execute(text(f"""
        CREATE OR REPLACE FUNCTION {function_name}()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO audit.admin_actions (
                admin_id, action_type, target_type, target_id, 
                old_values, new_values, created_at
            )
            VALUES (
                current_setting('app.current_user_id', true)::uuid,
                TG_OP,
                '{table_name}',
                COALESCE(NEW.id, OLD.id),
                to_jsonb(OLD),
                to_jsonb(NEW),
                NOW()
            );
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    """))
    
    # Create trigger
    op.execute(text(f"""
        CREATE TRIGGER {trigger_name}
        AFTER INSERT OR UPDATE OR DELETE ON app.{table_name}
        FOR EACH ROW EXECUTE FUNCTION {function_name}();
    """))


# =============================================================================
# Run migrations
# =============================================================================
if __name__ == '__main__':
    run_migrations()
