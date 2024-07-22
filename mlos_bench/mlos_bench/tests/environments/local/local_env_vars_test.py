#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for passing shell environment variables into LocalEnv scripts."""
import sys

import pytest

from mlos_bench.tests.environments import check_env_success
from mlos_bench.tests.environments.local import create_local_env
from mlos_bench.tunables.tunable_groups import TunableGroups


def _run_local_env(tunable_groups: TunableGroups, shell_subcmd: str, expected: dict) -> None:
    """Check that LocalEnv can set shell environment variables."""
    local_env = create_local_env(
        tunable_groups,
        {
            "const_args": {
                "const_arg": 111,  # Passed into "shell_env_params"
                "other_arg": 222,  # NOT passed into "shell_env_params"
            },
            "tunable_params": ["kernel"],
            "shell_env_params": [
                "const_arg",  # From "const_arg"
                "kernel_sched_latency_ns",  # From "tunable_params"
            ],
            "run": [
                "echo const_arg,other_arg,unknown_arg,kernel_sched_latency_ns > output.csv",
                f"echo {shell_subcmd} >> output.csv",
            ],
            "read_results_file": "output.csv",
        },
    )

    check_env_success(local_env, tunable_groups, expected, [])


@pytest.mark.skipif(sys.platform == "win32", reason="sh-like shell only")
def test_local_env_vars_shell(tunable_groups: TunableGroups) -> None:
    """Check that LocalEnv can set shell environment variables in sh-like shell."""
    _run_local_env(
        tunable_groups,
        shell_subcmd="$const_arg,$other_arg,$unknown_arg,$kernel_sched_latency_ns",
        expected={
            "const_arg": 111,  # From "const_args"
            "other_arg": float("NaN"),  # Not included in "shell_env_params"
            "unknown_arg": float("NaN"),  # Unknown/undefined variable
            "kernel_sched_latency_ns": 2000000,  # From "tunable_params"
        },
    )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_local_env_vars_windows(tunable_groups: TunableGroups) -> None:
    """Check that LocalEnv can set shell environment variables on Windows / cmd
    shell.
    """
    _run_local_env(
        tunable_groups,
        shell_subcmd=r"%const_arg%,%other_arg%,%unknown_arg%,%kernel_sched_latency_ns%",
        expected={
            "const_arg": 111,  # From "const_args"
            "other_arg": r"%other_arg%",  # Not included in "shell_env_params"
            "unknown_arg": r"%unknown_arg%",  # Unknown/undefined variable
            "kernel_sched_latency_ns": 2000000,  # From "tunable_params"
        },
    )
