#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test fixtures for mlos_bench storage."""

import json
import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from importlib.resources import files
from random import seed as rand_seed

import pytest
from fasteners import InterProcessLock
from pytest_docker.plugin import Services as DockerServices
from pytest_lazy_fixtures.lazy_fixture import lf as lazy_fixture

from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.schedulers.sync_scheduler import SyncScheduler
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.storage.storage_factory import from_config
from mlos_bench.tests import DOCKER, SEED, wait_docker_service_healthy
from mlos_bench.tests.storage import (
    CONFIG_TRIAL_REPEAT_COUNT,
    MAX_TRIALS,
    TRIAL_RUNNER_COUNT,
)
from mlos_bench.tests.storage.sql import (
    MYSQL_TEST_SERVER_NAME,
    PGSQL_TEST_SERVER_NAME,
    SqlTestServerInfo,
)
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name

# Try to test multiple DBMS engines.
DOCKER_DBMS_FIXTURES = []
if DOCKER:
    DOCKER_DBMS_FIXTURES = [
        lazy_fixture("mysql_storage"),
        lazy_fixture("postgres_storage"),
    ]


@pytest.fixture(scope="session")
def mysql_storage_info(
    docker_hostname: str,
    docker_compose_project_name: str,
    locked_docker_services: DockerServices,
) -> SqlTestServerInfo:
    """Fixture for getting mysql storage connection info."""
    storage_info = SqlTestServerInfo(
        compose_project_name=docker_compose_project_name,
        service_name=MYSQL_TEST_SERVER_NAME,
        hostname=docker_hostname,
    )
    wait_docker_service_healthy(
        locked_docker_services,
        storage_info.compose_project_name,
        storage_info.service_name,
    )

    return storage_info


@pytest.fixture(scope="session")
def postgres_storage_info(
    docker_hostname: str,
    docker_compose_project_name: str,
    locked_docker_services: DockerServices,
) -> SqlTestServerInfo:
    """Fixture for getting postgres storage connection info."""
    storage_info = SqlTestServerInfo(
        compose_project_name=docker_compose_project_name,
        service_name=PGSQL_TEST_SERVER_NAME,
        hostname=docker_hostname,
    )
    wait_docker_service_healthy(
        locked_docker_services,
        storage_info.compose_project_name,
        storage_info.service_name,
    )
    return storage_info


@contextmanager
def _create_storage_from_test_server_info(
    config_file: str,
    test_server_info: SqlTestServerInfo,
    shared_temp_dir: str,
    short_testrun_uid: str,
) -> Generator[SqlStorage]:
    """
    Creates a SqlStorage instance from the given test server info.

    Notes
    -----
    Resets the schema as a cleanup operation on return from the function scope
    fixture so each test gets a fresh storage instance.
    Uses a file lock to ensure that only one test can access the storage at a time.

    Yields
    ------
    SqlStorage
    """
    sql_storage_name = test_server_info.service_name
    with InterProcessLock(
        path_join(shared_temp_dir, f"{sql_storage_name}-{short_testrun_uid}.lock")
    ):
        global_config = {
            "host": test_server_info.hostname,
            "port": test_server_info.get_port() or 0,
            "database": test_server_info.database,
            "username": test_server_info.username,
            "password": test_server_info.password,
            "lazy_schema_create": True,
        }
        storage = from_config(
            config_file,
            global_configs=[json.dumps(global_config)],
        )
        assert isinstance(storage, SqlStorage)
        try:
            yield storage
        finally:
            # Cleanup the storage on return
            storage._reset_schema(force=True)  # pylint: disable=protected-access


@pytest.fixture(scope="function")
def mysql_storage(
    mysql_storage_info: SqlTestServerInfo,
    shared_temp_dir: str,
    short_testrun_uid: str,
) -> Generator[SqlStorage]:
    """
    Fixture of a MySQL backed SqlStorage engine.

    See Also
    --------
    _create_storage_from_test_server_info
    """
    with _create_storage_from_test_server_info(
        path_join(str(files("mlos_bench.config")), "storage", "mysql.jsonc"),
        mysql_storage_info,
        shared_temp_dir,
        short_testrun_uid,
    ) as storage:
        yield storage


@pytest.fixture(scope="function")
def postgres_storage(
    postgres_storage_info: SqlTestServerInfo,
    shared_temp_dir: str,
    short_testrun_uid: str,
) -> Generator[SqlStorage]:
    """
    Fixture of a Postgres backed SqlStorage engine.

    See Also
    --------
    _create_storage_from_test_server_info
    """
    with _create_storage_from_test_server_info(
        path_join(str(files("mlos_bench.config")), "storage", "postgresql.jsonc"),
        postgres_storage_info,
        shared_temp_dir,
        short_testrun_uid,
    ) as storage:
        yield storage


@pytest.fixture
def sqlite_storage() -> Generator[SqlStorage]:
    """
    Fixture for file based SQLite storage in a temporary directory.

    Yields
    ------
    Generator[SqlStorage]

    Notes
    -----
    Can't be used in parallel tests on Windows.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "mlos_bench.sqlite")
        config_str = json.dumps(
            {
                "class": "mlos_bench.storage.sql.storage.SqlStorage",
                "config": {
                    "drivername": "sqlite",
                    "database": db_path,
                    "lazy_schema_create": False,
                },
            }
        )

        storage = from_config(config_str)
        assert isinstance(storage, SqlStorage)
        storage.update_schema()
        yield storage
        storage.dispose()


@pytest.fixture
def storage() -> SqlStorage:
    """Test fixture for in-memory SQLite3 storage."""
    return SqlStorage(
        service=None,
        config={
            "drivername": "sqlite",
            "database": ":memory:",
            # "database": "mlos_bench.pytest.db",
        },
    )


@pytest.fixture
def exp_storage(
    storage: SqlStorage,
    tunable_groups: TunableGroups,
) -> Generator[SqlStorage.Experiment]:
    """
    Test fixture for Experiment using in-memory SQLite3 storage.

    Note: It has already entered the context upon return.
    """
    with storage.experiment(
        experiment_id="Test-001",
        trial_id=1,
        root_env_config="environment.jsonc",
        description="pytest experiment",
        tunables=tunable_groups,
        opt_targets={"score": "min"},
    ) as exp:
        yield exp
    # pylint: disable=protected-access
    assert not exp._in_context


@pytest.fixture
def exp_no_tunables_storage(
    storage: SqlStorage,
) -> Generator[SqlStorage.Experiment]:
    """
    Test fixture for Experiment using in-memory SQLite3 storage.

    Note: It has already entered the context upon return.
    """
    empty_config: dict = {}
    with storage.experiment(
        experiment_id="Test-003",
        trial_id=1,
        root_env_config="environment.jsonc",
        description="pytest experiment - no tunables",
        tunables=TunableGroups(empty_config),
        opt_targets={"score": "min"},
    ) as exp:
        yield exp
    # pylint: disable=protected-access
    assert not exp._in_context


@pytest.fixture
def mixed_numerics_exp_storage(
    storage: SqlStorage,
    mixed_numerics_tunable_groups: TunableGroups,
) -> Generator[SqlStorage.Experiment]:
    """
    Test fixture for an Experiment with mixed numerics tunables using in-memory SQLite3
    storage.

    Note: It has already entered the context upon return.
    """
    with storage.experiment(
        experiment_id="Test-002",
        trial_id=1,
        root_env_config="dne.jsonc",
        description="pytest experiment",
        tunables=mixed_numerics_tunable_groups,
        opt_targets={"score": "min"},
    ) as exp:
        yield exp
    # pylint: disable=protected-access
    assert not exp._in_context


def _dummy_run_exp(
    storage: SqlStorage,
    exp: SqlStorage.Experiment,
) -> ExperimentData:
    """
    Generates data by doing a simulated run of the given experiment.

    Parameters
    ----------
    storage : SqlStorage
        The storage object to use.
    exp : SqlStorage.Experiment
        The experiment to "run".
        Note: this particular object won't be updated, but a new one will be created
        from its metadata.

    Returns
    -------
    ExperimentData
        The data generated by the simulated run.
    """
    # pylint: disable=too-many-locals

    rand_seed(SEED)

    trial_runners: list[TrialRunner] = []
    global_config: dict = {}
    config_loader = ConfigPersistenceService()
    tunable_params = ",".join(f'"{name}"' for name in exp.tunables.get_covariant_group_names())
    mock_env_json = f"""
    {{
        "class": "mlos_bench.environments.mock_env.MockEnv",
        "name": "Test Env",
        "config": {{
            "tunable_params": [{tunable_params}],
            "mock_env_seed": {SEED},
            "mock_env_range": [60, 120],
            "mock_env_metrics": ["score"]
        }}
    }}
    """
    trial_runners = TrialRunner.create_from_json(
        config_loader=config_loader,
        global_config=global_config,
        tunable_groups=exp.tunables,
        env_json=mock_env_json,
        svcs_json=None,
        num_trial_runners=TRIAL_RUNNER_COUNT,
    )

    opt = MockOptimizer(
        tunables=exp.tunables,
        config={
            "optimization_targets": exp.opt_targets,
            "seed": SEED,
            # This should be the default, so we leave it omitted for now to test the default.
            # But the test logic relies on this (e.g., trial 1 is config 1 is the
            # default values for the tunable params)
            # "start_with_defaults": True,
            "max_suggestions": MAX_TRIALS,
        },
        global_config=global_config,
    )

    scheduler = SyncScheduler(
        # All config values can be overridden from global config
        config={
            "experiment_id": exp.experiment_id,
            "trial_id": exp.trial_id,
            "config_id": -1,
            "trial_config_repeat_count": CONFIG_TRIAL_REPEAT_COUNT,
            "max_trials": MAX_TRIALS,
        },
        global_config=global_config,
        trial_runners=trial_runners,
        optimizer=opt,
        storage=storage,
        root_env_config=exp.root_env_config,
    )

    # Add some trial data to that experiment by "running" it.
    with scheduler:
        scheduler.start()
        scheduler.teardown()

    return storage.experiments[exp.experiment_id]


@pytest.fixture
def exp_data(
    storage: SqlStorage,
    exp_storage: SqlStorage.Experiment,
) -> ExperimentData:
    """Test fixture for ExperimentData."""
    return _dummy_run_exp(storage, exp_storage)


@pytest.fixture
def exp_no_tunables_data(
    storage: SqlStorage,
    exp_no_tunables_storage: SqlStorage.Experiment,
) -> ExperimentData:
    """Test fixture for ExperimentData with no tunable configs."""
    return _dummy_run_exp(storage, exp_no_tunables_storage)


@pytest.fixture
def mixed_numerics_exp_data(
    storage: SqlStorage,
    mixed_numerics_exp_storage: SqlStorage.Experiment,
) -> ExperimentData:
    """Test fixture for ExperimentData with mixed numerical tunable types."""
    return _dummy_run_exp(storage, mixed_numerics_exp_storage)
