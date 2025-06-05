#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Alembic environment script."""
# pylint: disable=no-member

import logging
import sys
from logging.config import fileConfig

from alembic import context
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, engine_from_config, pool
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import Column as SchemaColumn
from sqlalchemy.sql.schema import Column as MetadataColumn
from sqlalchemy.types import TypeEngine

from mlos_bench.storage.sql.schema import DbSchema

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# Don't override the mlos_bench or pytest loggers though.
if config.config_file_name is not None and "alembic" in sys.argv[0]:
    fileConfig(config.config_file_name)
alembic_logger = logging.getLogger("alembic")

# add your model's MetaData object here
# for 'autogenerate' support
# NOTE: We override the alembic.ini file programmatically in storage/sql/schema.py
# However, the alembic.ini file value is used during alembic CLI operations
# (e.g., dev ops extending the schema).
sqlalchemy_url = config.get_main_option("sqlalchemy.url")
if not sqlalchemy_url:
    raise ValueError("Missing sqlalchemy.url: schema changes may not be accurate.")
engine = create_engine(sqlalchemy_url)
alembic_logger.info("engine.url %s", str(engine.url))
target_metadata = DbSchema(engine=engine).meta

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def fq_class_name(t: object) -> str:
    """Return the fully qualified class name of a type."""
    return t.__module__ + "." + t.__class__.__name__


def custom_compare_types(
    migration_context: MigrationContext,
    inspected_column: SchemaColumn | None,
    metadata_column: MetadataColumn,
    inspected_type: TypeEngine,
    metadata_type: TypeEngine,
) -> bool | None:
    """
    Custom column type comparator.

    See `Comparing Types
    <https://alembic.sqlalchemy.org/en/latest/autogenerate.html#comparing-types>`_
    documentation for more details.

    Parameters
    ----------

    Notes
    -----
    In the case of a MySQL DateTime variant, it makes sure that the floating
    point accuracy is met.

    Returns
    -------
    result : bool | None
        Returns True if the column specifications don't match the column (i.e.,
        a change is needed).
        Returns False when the column specification and column match.
        Returns None to fallback to the default comparator logic.
    """
    metadata_dialect_type = metadata_type.dialect_impl(migration_context.dialect)
    if alembic_logger.isEnabledFor(logging.DEBUG):
        alembic_logger.debug(
            (
                "Comparing columns: "
                "inspected_column: [%s] %s and "
                "metadata_column: [%s (%s)] %s "
                "inspected_column.__dict__: %s\n"
                "inspected_column.dialect_options: %s\n"
                "inspected_column.dialect_kwargs: %s\n"
                "inspected_type.__dict__: %s\n"
                "metadata_column.__dict__: %s\n"
                "metadata_type.__dict__: %s\n"
                "metadata_dialect_type.__dict__: %s\n"
            ),
            fq_class_name(inspected_type),
            inspected_column,
            fq_class_name(metadata_type),
            fq_class_name(metadata_dialect_type),
            metadata_column,
            inspected_column.__dict__,
            dict(inspected_column.dialect_options) if inspected_column is not None else None,
            dict(inspected_column.dialect_kwargs) if inspected_column is not None else None,
            inspected_type.__dict__,
            metadata_column.__dict__,
            metadata_type.__dict__,
            metadata_dialect_type.__dict__,
        )

    # Implement a more detailed DATETIME precision comparison for MySQL.
    # Note: Currently also handles MariaDB.
    if migration_context.dialect.name == "mysql":
        if isinstance(metadata_dialect_type, (mysql.DATETIME, mysql.TIMESTAMP)):
            if not isinstance(inspected_type, type(metadata_dialect_type)):
                alembic_logger.info(
                    "inspected_type %s does not match metadata_dialect_type %s",
                    fq_class_name(inspected_type),
                    fq_class_name(metadata_dialect_type),
                )
                return True
            else:
                if inspected_type.fsp != metadata_dialect_type.fsp:
                    alembic_logger.info(
                        "inspected_type.fsp (%s) and metadata_dialect_type.fsp (%s) don't match",
                        inspected_type.fsp,
                        metadata_dialect_type.fsp,
                    )
                    return True

                if inspected_type.timezone != metadata_dialect_type.timezone:
                    alembic_logger.info(
                        (
                            "inspected_type.timezone (%s) and "
                            "metadata_dialect_type.timezone (%s) don't match"
                        ),
                        inspected_type.timezone,
                        metadata_dialect_type.timezone,
                    )
                    return True

    if alembic_logger.isEnabledFor(logging.DEBUG):
        alembic_logger.debug(
            (
                "Using default compare_type behavior for "
                "inspected_column: [%s] %s and "
                "metadata_column: [%s (%s)] %s (see above for details).\n"
            ),
            fq_class_name(inspected_type),
            inspected_column,
            fq_class_name(metadata_type),
            fq_class_name(metadata_dialect_type),
            metadata_column,
        )
    return None  # fallback to default comparison behavior


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
        compare_type=custom_compare_types,
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
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=custom_compare_types,
            )

            with context.begin_transaction():
                context.run_migrations()
    else:
        context.configure(
            connection=connectable,
            target_metadata=target_metadata,
            compare_type=custom_compare_types,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
