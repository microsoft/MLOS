#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Alembic environment script."""
# pylint: disable=no-member

import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from mlos_bench.storage.sql.schema import DbSchema

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# Don't override the mlos_bench or pytest loggers though.
if config.config_file_name is not None and "alembic" in sys.argv[0]:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = DbSchema(engine=None).meta

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine is
    acceptable here as well.  By skipping the Engine creation we don't even need a DBAPI
    to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the
    context.
    """
    connectable = config.attributes.get("connection", None)

    if connectable is None:
        # only create Engine if we don't have a Connection
        # from the outside
        connectable = engine_from_config(
            config.get_section(config.config_ini_section) or {},
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)

            with context.begin_transaction():
                context.run_migrations()
    else:
        context.configure(connection=connectable, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
