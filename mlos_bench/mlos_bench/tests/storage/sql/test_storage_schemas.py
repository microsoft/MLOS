#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test sql schemas for mlos_bench storage."""

import pytest
from pytest_lazy_fixtures.lazy_fixture import lf as lazy_fixture

from alembic.migration import MigrationContext
from sqlalchemy import inspect

from mlos_bench.storage.sql.storage import SqlStorage

from mlos_bench.tests import DOCKER

# NOTE: This value is hardcoded to the latest revision in the alembic versions directory.
# It could also be obtained programmatically using the "alembic heads" command or heads() API.
# See Also: schema.py for an example of programmatic alembic config access.
CURRENT_ALEMBIC_HEAD = "8928a401115b"

# Try to test multiple DBMS engines.
docker_dbms_fixtures = []
if DOCKER:
    docker_dbms_fixtures = [
        lazy_fixture("mysql_storage"),
        lazy_fixture("postgres_storage"),
    ]
@pytest.mark.parameterize(
        ["some_sql_storage_fixture"], [
            lazy_fixture("sql_storage"),
            *docker_dbms_fixtures,
        ]
)
def test_storage_schemas(some_sql_storage_fixture: SqlStorage) -> None:
    """Test storage schema creation."""
    eng = some_sql_storage_fixture._engine  # pylint: disable=protected-access
    with eng.connect() as conn:  # pylint: disable=protected-access
        inspector = inspect(conn)
        # Make sure the "trial_runner_id" column exists.
        # (i.e., the latest schema has been applied)
        assert any(
            column["name"] == "trial_runner_id" for column in inspect(conn).get_columns("trial")
        )
        # Make sure the "alembic_version" table exists and is appropriately stamped.
        assert inspector.has_table("alembic_version")
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        assert (
            current_rev == CURRENT_ALEMBIC_HEAD
        ), f"Expected {CURRENT_ALEMBIC_HEAD}, got {current_rev}"
