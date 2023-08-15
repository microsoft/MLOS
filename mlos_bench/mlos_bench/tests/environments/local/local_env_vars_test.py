#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for passing shell environment variables into LocalEnv scripts.
"""
import pytest

from mlos_bench.environments.local.local_env import LocalEnv
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.tunables.tunable_groups import TunableGroups


def test_local_env_vars(tunable_groups: TunableGroups) -> None:
    """
    Check that LocalEnv can set shell environment variables.
    """
    local_env = LocalEnv(
        name="Test Local Env",
        config={
            "const_args": {
                "const_arg": 111,  # Passed into "shell_env_params"
                "other_arg": 222,  # NOT passed into "shell_env_params"
            },
            "tunable_params": ["kernel"],
            "shell_env_params": [
                "const_arg",                # From "const_arg"
                "kernel_sched_latency_ns",  # From "tunable_params"
            ],
            "run": [
                "echo const_arg,other_arg,unknown_arg,kernel_sched_latency_ns > output.csv",
                "echo $const_arg,$other_arg,$unknown_arg,$kernel_sched_latency_ns >> output.csv",
            ],
            "read_results_file": "output.csv",
        },
        tunables=tunable_groups,
        service=LocalExecService(parent=ConfigPersistenceService()),
    )
    with local_env as env_context:
        assert env_context.setup(tunable_groups)
        (status, data) = env_context.run()
        assert status.is_succeeded()
        assert data == pytest.approx({
            "const_arg": 111,                       # From "const_args"
            "other_arg": float("NaN"),              # Not included in "shell_env_params"
            "unknown_arg": float("NaN"),            # Unknown/undefined variable
            "kernel_sched_latency_ns": 2000000,     # From "tunable_params"
        }, nan_ok=True)
