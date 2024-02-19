#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the composition of several LocalEnv benchmark environments.
"""
import pytz
import sys
from datetime import datetime, timedelta

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tests.environments import check_env_success
from mlos_bench.tests.environments.local import create_composite_local_env


def test_composite_env(tunable_groups: TunableGroups) -> None:
    """
    Produce benchmark and telemetry data in TWO local environments
    and combine the results.
    Also checks that global configs flow down at least one level of CompositeEnv
    to its children without being explicitly specified in the CompositeEnv so they
    can be used in the shell_envs by its children.
    See Also: http://github.com/microsoft/MLOS/issues/501
    """
    ts1 = datetime.utcnow().astimezone(pytz.UTC)
    ts1 -= timedelta(microseconds=ts1.microsecond)  # Round to a second
    ts2 = ts1 + timedelta(minutes=2)

    time_str1 = ts1.strftime("%Y-%m-%d %H:%M:%S %z")
    time_str2 = ts2.strftime("%Y-%m-%d %H:%M:%S %z")

    (var_prefix, var_suffix) = ("%", "%") if sys.platform == 'win32' else ("$", "")

    env = create_composite_local_env(
        tunable_groups=tunable_groups,
        global_config={
            "reads": 2222,
            "writes": 1111,
        },
        params={
            "const_args": {
                "latency": 4.2,
                "throughput": 768,
                "errors": 0,
            }
        },
        local_configs=[
            {
                "const_args": {
                    "latency": 3.3,
                    "reads": 0,
                },
                "required_args": ["errors", "reads"],
                "shell_env_params": [
                    "latency",  # const_args overridden by the composite env
                    "errors",   # Comes from the parent const_args
                    "reads"     # const_args overridden by the global config
                ],
                "run": [
                    "echo 'metric,value' > output.csv",
                    f"echo 'latency,{var_prefix}latency{var_suffix}' >> output.csv",
                    f"echo 'errors,{var_prefix}errors{var_suffix}' >> output.csv",
                    f"echo 'reads,{var_prefix}reads{var_suffix}' >> output.csv",
                    "echo '-------------------'",  # This output does not go anywhere
                    "echo 'timestamp,metric,value' > telemetry.csv",
                    f"echo {time_str1},cpu_load,0.64 >> telemetry.csv",
                    f"echo {time_str1},mem_usage,5120 >> telemetry.csv",
                ],
                "read_results_file": "output.csv",
                "read_telemetry_file": "telemetry.csv",
            },
            {
                "const_args": {
                    "throughput": 999,
                    "score": 0.97,
                },
                "required_args": ["writes"],
                "shell_env_params": [
                    "throughput",   # const_args overridden by the composite env
                    "score",        # Comes from the local const_args
                    "writes"        # Comes straight from the global config
                ],
                "run": [
                    "echo 'metric,value' > output.csv",
                    f"echo 'throughput,{var_prefix}throughput{var_suffix}' >> output.csv",
                    f"echo 'score,{var_prefix}score{var_suffix}' >> output.csv",
                    f"echo 'writes,{var_prefix}writes{var_suffix}' >> output.csv",
                    "echo '-------------------'",  # This output does not go anywhere
                    "echo 'timestamp,metric,value' > telemetry.csv",
                    f"echo {time_str2},cpu_load,0.79 >> telemetry.csv",
                    f"echo {time_str2},mem_usage,40960 >> telemetry.csv",
                ],
                "read_results_file": "output.csv",
                "read_telemetry_file": "telemetry.csv",
            }
        ]
    )

    check_env_success(
        env, tunable_groups,
        expected_results={
            "latency": 4.2,
            "throughput": 768.0,
            "score": 0.97,
            "errors": 0.0,
            "reads": 2222.0,
            "writes": 1111.0,
        },
        expected_telemetry=[
            (ts1, "cpu_load", 0.64),
            (ts1, "mem_usage", 5120.0),
            (ts2, "cpu_load", 0.79),
            (ts2, "mem_usage", 40960.0),
        ],
    )
