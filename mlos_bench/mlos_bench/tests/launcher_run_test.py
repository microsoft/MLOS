#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests to check the main CLI launcher."""
import os
import re
from typing import List

import pytest

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name


@pytest.fixture
def root_path() -> str:
    """Root path of mlos_bench project."""
    return path_join(os.path.dirname(__file__), "../../..", abs_path=True)


@pytest.fixture
def local_exec_service() -> LocalExecService:
    """Test fixture for LocalExecService."""
    return LocalExecService(
        parent=ConfigPersistenceService(
            {
                "config_path": [
                    "mlos_bench/config",
                    "mlos_bench/examples",
                ]
            }
        )
    )


def _launch_main_app(
    root_path: str,
    local_exec_service: LocalExecService,
    cli_config: str,
    re_expected: List[str],
) -> None:
    """Run mlos_bench command-line application with given config and check the results
    in the log.
    """
    with local_exec_service.temp_dir_context() as temp_dir:

        # Test developers note: for local debugging,
        # uncomment the following line to use a known file path that can be examined:
        # temp_dir = '/tmp'
        log_path = path_join(temp_dir, "mock-test.log")
        (return_code, _stdout, _stderr) = local_exec_service.local_exec(
            [
                "./mlos_bench/mlos_bench/run.py"
                + " --config_path ./mlos_bench/mlos_bench/tests/config/"
                + f" {cli_config} --log_file '{log_path}'"
            ],
            cwd=root_path,
        )
        assert return_code == 0

        try:
            iter_expected = iter(re_expected)
            re_log = re.compile(next(iter_expected))
            with open(log_path, "rt", encoding="utf-8") as fh_out:
                for line in fh_out:
                    if re_log.match(line):
                        re_log = re.compile(next(iter_expected))
            assert False, f"Pattern not found: '{re_log.pattern}'"
        except StopIteration:
            pass  # Success: all patterns found


_RE_DATE = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}"


def test_launch_main_app_bench(root_path: str, local_exec_service: LocalExecService) -> None:
    """Run mlos_bench command-line application with mock benchmark config and default
    tunable values and check the results in the log.
    """
    _launch_main_app(
        root_path,
        local_exec_service,
        " --config cli/mock-bench.jsonc"
        + " --trial_config_repeat_count 5"
        + " --mock_env_seed -1",  # Deterministic Mock Environment.
        [
            f"^{_RE_DATE} run\\.py:\\d+ " + r"_main INFO Final score: \{'score': 67\.40\d+\}\s*$",
        ],
    )


def test_launch_main_app_bench_values(
    root_path: str,
    local_exec_service: LocalExecService,
) -> None:
    """Run mlos_bench command-line application with mock benchmark config and user-
    specified tunable values and check the results in the log.
    """
    _launch_main_app(
        root_path,
        local_exec_service,
        " --config cli/mock-bench.jsonc"
        + " --tunable_values tunable-values/tunable-values-example.jsonc"
        + " --trial_config_repeat_count 5"
        + " --mock_env_seed -1",  # Deterministic Mock Environment.
        [
            f"^{_RE_DATE} run\\.py:\\d+ " + r"_main INFO Final score: \{'score': 67\.11\d+\}\s*$",
        ],
    )


def test_launch_main_app_opt(root_path: str, local_exec_service: LocalExecService) -> None:
    """Run mlos_bench command-line application with mock optimization config and check
    the results in the log.
    """
    _launch_main_app(
        root_path,
        local_exec_service,
        "--config cli/mock-opt.jsonc"
        + " --trial_config_repeat_count 3"
        + " --max_suggestions 3"
        + " --mock_env_seed 42",  # Noisy Mock Environment.
        [
            # Iteration 1: Expect first value to be the baseline
            f"^{_RE_DATE} mlos_core_optimizer\\.py:\\d+ "
            + r"bulk_register DEBUG Warm-up END: .* :: \{'score': 64\.53\d+\}$",
            # Iteration 2: The result may not always be deterministic
            f"^{_RE_DATE} mlos_core_optimizer\\.py:\\d+ "
            + r"bulk_register DEBUG Warm-up END: .* :: \{'score': \d+\.\d+\}$",
            # Iteration 3: non-deterministic (depends on the optimizer)
            f"^{_RE_DATE} mlos_core_optimizer\\.py:\\d+ "
            + r"bulk_register DEBUG Warm-up END: .* :: \{'score': \d+\.\d+\}$",
            # Final result: baseline is the optimum for the mock environment
            f"^{_RE_DATE} run\\.py:\\d+ " + r"_main INFO Final score: \{'score': 64\.53\d+\}\s*$",
        ],
    )
