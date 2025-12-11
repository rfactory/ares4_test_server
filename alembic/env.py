import os
import sys
# Add the project's root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy_utils import database_exists, create_database

from alembic import context

from app.database import Base # Moved up
from app.core.config import settings # Moved up
# Import all models here so that Base has them registered
from app.models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def create_database_if_not_exists(db_url: str):
    """Creates the database if it does not exist."""
    try:
        if not database_exists(db_url):
            print(f"Database at {db_url} does not exist. Creating...")
            create_database(db_url, template='template0')
            print(f"Database at {db_url} created.")
        else:
            print(f"Database at {db_url} already exists.")
    except Exception as e:
        print(f"Error connecting to default database or creating target database: {e}")
        sys.exit(1)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # --- Custom: Ensure database exists before connecting ---
    create_database_if_not_exists(settings.DATABASE_URL)
    # --- End Custom ---

    # Use DATABASE_URL from our app settings for online mode
    configuration = config.get_section(config.config_ini_section, {})
    configuration['sqlalchemy.url'] = settings.DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
