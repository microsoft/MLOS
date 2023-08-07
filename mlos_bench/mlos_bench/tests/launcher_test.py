#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests to check the main CLI launcher.
"""
import os
import re

import pytest

from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name


@pytest.fixture
def root_path() -> str:
    """
    Root path of mlos_bench project.
    """
    return path_join(os.path.dirname(__file__), "../../..", abs_path=True)


@pytest.fixture
def local_exec_service() -> LocalExecService:
    """
    Test fixture for LocalExecService.
    """
    return LocalExecService(parent=ConfigPersistenceService({
        "config_path": [
            "mlos_bench/config",
            "mlos_bench/examples",
        ]
    }))


def _launch_main_app(root_path: str, local_exec_service: LocalExecService,
                     cli_config: str, re_expected: list[str]) -> None:
    """
    Run mlos_bench command-line application with given config
    and check the results in the log.
    """
    with local_exec_service.temp_dir_context() as temp_dir:

        log_path = path_join(temp_dir, "mock-bench.log")
        (return_code, _stdout, _stderr) = local_exec_service.local_exec(
            [f"./mlos_bench/mlos_bench/run.py {cli_config} --log_file '{log_path}'"],
            cwd=root_path)
        assert return_code == 0

        try:
            iter_expected = iter(re_expected)
            re_log = re.compile(next(iter_expected))
            with open(log_path, "rt", encoding="utf-8") as fh_out:
                for ln in fh_out:
                    if re_log.match(ln):
                        re_log = re.compile(next(iter_expected))
            assert False, f"Pattern not found: '{re_log.pattern}'"
        except StopIteration:
            pass  # Success: all patterns found


def test_launch_main_app_bench(root_path: str, local_exec_service: LocalExecService) -> None:
    """
    Run mlos_bench command-line application with mock benchmark config
    and check the results in the log.
    """
    _launch_main_app(
        root_path, local_exec_service,
        "--config mlos_bench/mlos_bench/tests/config/cli/mock-bench.jsonc",
        [
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} run\.py:\d+ " +
            r"_optimize INFO Env: Mock environment best score: 65\.67\d+\s*$",
        ]
    )


def test_launch_main_app_opt(root_path: str, local_exec_service: LocalExecService) -> None:
    """
    Run mlos_bench command-line application with mock optimization config
    and check the results in the log.
    """
    _launch_main_app(
        root_path, local_exec_service,
        "--config mlos_bench/mlos_bench/tests/config/cli/mock-opt.jsonc --max_iterations 3",
        [
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} mlos_core_optimizer\.py:\d+ " +
            r"register DEBUG Score: 65\.67\d+ Dataframe:\s*$",

            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} mlos_core_optimizer\.py:\d+ " +
            r"register DEBUG Score: 75\.0\d+ Dataframe:\s*$",

            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} mlos_core_optimizer\.py:\d+ " +
            r"register DEBUG Score: 82\.617\d+ Dataframe:\s*$",

            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} run\.py:\d+ " +
            r"_optimize INFO Env: Mock environment best score: 65\.67\d+\s*$",
        ]
    )
