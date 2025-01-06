#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test sql schemas for mlos_bench storage."""

from alembic.migration import MigrationContext
from sqlalchemy import inspect

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.sql.storage import SqlStorage

# NOTE: This value is hardcoded to the latest revision in the alembic versions directory.
# It could also be obtained programmatically using the "alembic heads" command or heads() API.
# See Also: schema.py for an example of programmatic alembic config access.
CURRENT_ALEMBIC_HEAD = "f83fb8ae7fc4"


def test_storage_schemas(storage: SqlStorage) -> None:
    """Test storage schema creation."""
    eng = storage._engine  # pylint: disable=protected-access
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


# Note: this is a temporary test.  It will be removed and replaced with a more
# properly integrated test in #702.
def test_trial_runner_id_default(storage: SqlStorage, exp_data: ExperimentData) -> None:
    """Test that the new trial_runner_id column defaults to None."""
    assert exp_data.trials
    eng = storage._engine  # pylint: disable=protected-access
    schema = storage._schema  # pylint: disable=protected-access
    with eng.connect() as conn:
        trials = conn.execute(
            schema.trial_result.select().with_only_columns(
                schema.trial.c.trial_runner_id,
            )
        )
        # trial_runner_id is not currently fully implemented
        trial_row = trials.fetchone()
        assert trial_row
        assert trial_row.trial_runner_id is None
