#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test sql schemas for mlos_bench storage."""

import pytest
from alembic.migration import MigrationContext
from pytest_lazy_fixtures.lazy_fixture import lf as lazy_fixture
from sqlalchemy import inspect

from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.tests.storage.sql.fixtures import DOCKER_DBMS_FIXTURES

# NOTE: This value is hardcoded to the latest revision in the alembic versions directory.
# It could also be obtained programmatically using the "alembic heads" command or heads() API.
# See Also: schema.py for an example of programmatic alembic config access.
CURRENT_ALEMBIC_HEAD = "b61aa446e724"


# Try to test multiple DBMS engines.
@pytest.mark.parametrize(
    "some_sql_storage_fixture",
    [
        lazy_fixture("mem_storage"),
        lazy_fixture("sqlite_storage"),
        *DOCKER_DBMS_FIXTURES,
    ],
)
def test_storage_schemas(some_sql_storage_fixture: SqlStorage) -> None:
    """Test storage schema creation."""
    assert isinstance(some_sql_storage_fixture, SqlStorage)
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
