#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for loading scheduler config examples."""
import logging

import pytest

import mlos_bench.tests.optimizers.fixtures
import mlos_bench.tests.storage.sql.fixtures
from mlos_bench.config.schemas.config_schemas import ConfigSchema
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.schedulers.base_scheduler import Scheduler
from mlos_bench.schedulers.trial_runner import TrialRunner
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.storage.sql.storage import SqlStorage
from mlos_bench.tests.config import BUILTIN_TEST_CONFIG_PATH, locate_config_examples
from mlos_bench.util import get_class_from_name

mock_opt = mlos_bench.tests.optimizers.fixtures.mock_opt

storage = mlos_bench.tests.storage.sql.fixtures.storage



_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)

# pylint: disable=redefined-outer-name

# Get the set of configs to test.
CONFIG_TYPE = "schedulers"


def filter_configs(configs_to_filter: list[str]) -> list[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""
    return configs_to_filter


configs = locate_config_examples(
    ConfigPersistenceService.BUILTIN_CONFIG_PATH,
    CONFIG_TYPE,
    filter_configs,
)
assert configs

test_configs = locate_config_examples(
    BUILTIN_TEST_CONFIG_PATH,
    CONFIG_TYPE,
    filter_configs,
)
# assert test_configs
configs.extend(test_configs)


@pytest.mark.parametrize("config_path", configs)
def test_load_scheduler_config_examples(
    config_loader_service: ConfigPersistenceService,
    config_path: str,
    mock_env_config_path: str,
    trial_runners: list[TrialRunner],

    storage: SqlStorage,

    mock_opt: MockOptimizer,
) -> None:
    """Tests loading a config example."""
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    config = config_loader_service.load_config(config_path, ConfigSchema.SCHEDULER)
    assert isinstance(config, dict)
    cls = get_class_from_name(config["class"])
    assert issubclass(cls, Scheduler)
    global_config = {
        # Required configs generally provided by the Launcher.
        "experiment_id": f"test_experiment_{__name__}",
        "trial_id": 1,
    }
    # Make an instance of the class based on the config.
    scheduler_inst = config_loader_service.build_scheduler(
        config=config,
        global_config=global_config,
        trial_runners=trial_runners,
        optimizer=mock_opt,

        storage=storage,

        root_env_config=mock_env_config_path,
    )
    assert scheduler_inst is not None
    assert isinstance(scheduler_inst, cls)
