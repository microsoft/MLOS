#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Test the selection of tunables / tunable groups for the environment."""

from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_one_group(tunable_groups: TunableGroups) -> None:
    """Make sure only one tunable group is available to the environment."""
    env = MockEnv(
        name="Test Env",
        config={"tunable_params": ["provision"]},
        tunables=tunable_groups,
    )
    assert env.tunable_params.get_param_values() == {
        "vmSize": "Standard_B4ms",
    }


def test_two_groups(tunable_groups: TunableGroups) -> None:
    """Make sure only the selected tunable groups are available to the environment."""
    env = MockEnv(
        name="Test Env",
        config={"tunable_params": ["provision", "kernel"]},
        tunables=tunable_groups,
    )
    assert env.tunable_params.get_param_values() == {
        "vmSize": "Standard_B4ms",
        "kernel_sched_migration_cost_ns": -1,
        "kernel_sched_latency_ns": 2000000,
    }


def test_two_groups_setup(tunable_groups: TunableGroups) -> None:
    """Make sure only the selected tunable groups are available to the environment, the
    set is not changed after calling the `.setup()` method.
    """
    env = MockEnv(
        name="Test Env",
        config={
            "tunable_params": ["provision", "kernel"],
            "const_args": {
                "const_param1": 10,
                "const_param2": "foo",
            },
        },
        tunables=tunable_groups,
    )
    expected_params = {
        "vmSize": "Standard_B4ms",
        "kernel_sched_migration_cost_ns": -1,
        "kernel_sched_latency_ns": 2000000,
    }
    assert env.tunable_params.get_param_values() == expected_params

    with env as env_context:
        assert env_context.setup(tunable_groups)

    # Make sure the set of tunables does not change after the setup:
    assert env.tunable_params.get_param_values() == expected_params
    assert env.parameters == {
        **expected_params,
        "const_param1": 10,
        "const_param2": "foo",
    }


def test_zero_groups_implicit(tunable_groups: TunableGroups) -> None:
    """Make sure that no tunable groups are available to the environment by default."""
    env = MockEnv(name="Test Env", config={}, tunables=tunable_groups)
    assert env.tunable_params.get_param_values() == {}


def test_zero_groups_explicit(tunable_groups: TunableGroups) -> None:
    """Make sure that no tunable groups are available to the environment when explicitly
    specifying an empty list of tunable_params.
    """
    env = MockEnv(name="Test Env", config={"tunable_params": []}, tunables=tunable_groups)
    assert env.tunable_params.get_param_values() == {}


def test_zero_groups_implicit_setup(tunable_groups: TunableGroups) -> None:
    """Make sure that no tunable groups are available to the environment by default and
    it does not change after the setup.
    """
    env = MockEnv(
        name="Test Env",
        config={
            "const_args": {
                "const_param1": 10,
                "const_param2": "foo",
            },
        },
        tunables=tunable_groups,
    )
    assert env.tunable_params.get_param_values() == {}

    with env as env_context:
        assert env_context.setup(tunable_groups)

    # Make sure the set of tunables does not change after the setup:
    assert env.tunable_params.get_param_values() == {}
    assert env.parameters == {
        "const_param1": 10,
        "const_param2": "foo",
    }


def test_loader_level_include() -> None:
    """Make sure only the selected tunable groups are available to the environment, the
    set is not changed after calling the `.setup()` method.
    """
    env_json = {
        "class": "mlos_bench.environments.mock_env.MockEnv",
        "name": "Test Env",
        "include_tunables": ["environments/os/linux/boot/linux-boot-tunables.jsonc"],
        "config": {
            "tunable_params": ["linux-kernel-boot"],
            "const_args": {
                "const_param1": 10,
                "const_param2": "foo",
            },
        },
    }
    loader = ConfigPersistenceService(
        {
            "config_path": [
                "mlos_bench/config",
                "mlos_bench/examples",
            ]
        }
    )
    env = loader.build_environment(config=env_json, tunables=TunableGroups())
    expected_params = {
        "align_va_addr": "on",
        "idle": "halt",
        "ima.ahash_bufsize": 4096,
        "noautogroup": "",
        "nohugevmalloc": "",
        "nohalt": "",
        "nohz": "",
        "no-kvmapf": "",
        "nopvspin": "",
    }
    assert env.tunable_params.get_param_values() == expected_params

    expected_params["align_va_addr"] = "off"
    tunables = env.tunable_params.copy().assign({"align_va_addr": "off"})

    with env as env_context:
        assert env_context.setup(tunables)

    # Make sure the set of tunables does not change after the setup:
    assert env.parameters == {
        **expected_params,
        "const_param1": 10,
        "const_param2": "foo",
    }
    assert env.tunable_params.get_param_values() == expected_params
