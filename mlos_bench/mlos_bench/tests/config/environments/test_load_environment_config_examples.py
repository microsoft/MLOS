#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for loading environment config examples."""
import logging
from typing import List

import pytest

from mlos_bench.config.schemas.config_schemas import ConfigSchema
from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.composite_env import CompositeEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tests.config import locate_config_examples
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


# Get the set of configs to test.
CONFIG_TYPE = "environments"


def filter_configs(configs_to_filter: List[str]) -> List[str]:
    """If necessary, filter out json files that aren't for the module we're testing."""
    configs_to_filter = [
        config_path
        for config_path in configs_to_filter
        if not config_path.endswith("-tunables.jsonc")
    ]
    return configs_to_filter


configs = locate_config_examples(
    ConfigPersistenceService.BUILTIN_CONFIG_PATH,
    CONFIG_TYPE,
    filter_configs,
)
assert configs


@pytest.mark.parametrize("config_path", configs)
def test_load_environment_config_examples(
    config_loader_service: ConfigPersistenceService,
    config_path: str,
) -> None:
    """Tests loading an environment config example."""
    envs = load_environment_config_examples(config_loader_service, config_path)
    for env in envs:
        assert env is not None
        assert isinstance(env, Environment)


def load_environment_config_examples(
    config_loader_service: ConfigPersistenceService,
    config_path: str,
) -> List[Environment]:
    """Loads an environment config example."""
    # Make sure that any "required_args" are provided.
    global_config = config_loader_service.load_config(
        "experiments/experiment_test_config.jsonc",
        ConfigSchema.GLOBALS,
    )
    global_config.setdefault("trial_id", 1)  # normally populated by Launcher

    # Make sure we have the required services for the envs being used.
    mock_service_configs = [
        "services/local/mock/mock_local_exec_service.jsonc",
        "services/remote/mock/mock_fileshare_service.jsonc",
        "services/remote/mock/mock_network_service.jsonc",
        "services/remote/mock/mock_vm_service.jsonc",
        "services/remote/mock/mock_remote_exec_service.jsonc",
        "services/remote/mock/mock_auth_service.jsonc",
    ]

    tunable_groups = TunableGroups()  # base tunable groups that all others get built on

    for mock_service_config_path in mock_service_configs:
        mock_service_config = config_loader_service.load_config(
            mock_service_config_path,
            ConfigSchema.SERVICE,
        )
        config_loader_service.register(
            config_loader_service.build_service(
                config=mock_service_config,
                parent=config_loader_service,
            ).export()
        )

    envs = config_loader_service.load_environment_list(
        config_path,
        tunable_groups,
        global_config,
        service=config_loader_service,
    )
    return envs


composite_configs = locate_config_examples(
    ConfigPersistenceService.BUILTIN_CONFIG_PATH,
    "environments/root/",
)
assert composite_configs


@pytest.mark.parametrize("config_path", composite_configs)
def test_load_composite_env_config_examples(
    config_loader_service: ConfigPersistenceService,
    config_path: str,
) -> None:
    """Tests loading a composite env config example."""
    envs = load_environment_config_examples(config_loader_service, config_path)
    assert len(envs) == 1
    assert isinstance(envs[0], CompositeEnv)
    composite_env: CompositeEnv = envs[0]

    for child_env in composite_env.children:
        assert child_env is not None
        assert isinstance(child_env, Environment)
        assert child_env.tunable_params is not None

        checked_child_env_groups = set()
        for child_tunable, child_group in child_env.tunable_params:
            # Lookup that tunable in the composite env.
            assert child_tunable in composite_env.tunable_params
            (composite_tunable, composite_group) = composite_env.tunable_params.get_tunable(
                child_tunable
            )
            # Check that the tunables are the same object.
            assert child_tunable is composite_tunable
            if child_group.name not in checked_child_env_groups:
                assert child_group is composite_group
                checked_child_env_groups.add(child_group.name)

            # Check that when we change a child env, it's value is reflected in the
            # composite env as well.
            # That is to say, they refer to the same objects, despite having
            # potentially been loaded from separate configs.
            if child_tunable.is_categorical:
                old_cat_value = child_tunable.category
                assert child_tunable.value == old_cat_value
                assert child_group[child_tunable] == old_cat_value
                assert composite_env.tunable_params[child_tunable] == old_cat_value
                new_cat_value = [x for x in child_tunable.categories if x != old_cat_value][0]
                child_tunable.category = new_cat_value
                assert child_env.tunable_params[child_tunable] == new_cat_value
                assert composite_env.tunable_params[child_tunable] == child_tunable.category
            elif child_tunable.is_numerical:
                old_num_value = child_tunable.numerical_value
                assert child_tunable.value == old_num_value
                assert child_group[child_tunable] == old_num_value
                assert composite_env.tunable_params[child_tunable] == old_num_value
                child_tunable.numerical_value += 1
                assert child_env.tunable_params[child_tunable] == old_num_value + 1
                assert composite_env.tunable_params[child_tunable] == child_tunable.numerical_value
