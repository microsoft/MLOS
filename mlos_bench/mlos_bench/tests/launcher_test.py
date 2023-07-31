#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests to check the main CLI launcher.
"""
import os

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


def test_launch_main_app(root_path: str,
                         local_exec_service: LocalExecService) -> None:
    """
    Run mlos_bench command-line application with mock config and check the results in the log.
    """
    with local_exec_service.temp_dir_context() as temp_dir:

        log_path = path_join(temp_dir, "mock-bench.log")
        cmd = "./mlos_bench/mlos_bench/run.py" + \
              " --config mlos_bench/mlos_bench/tests/config/cli/mock-bench.jsonc" + \
              f" --log_file '{log_path}'"
        (return_code, _stdout, _stderr) = local_exec_service.local_exec([cmd], cwd=root_path)

        assert return_code == 0

        with open(log_path, "rt", encoding="utf-8") as fh_out:
            best_score_lines = [
                ln.strip() for ln in fh_out.readlines()
                if " INFO Env: Mock environment best score: " in ln
            ]
            assert len([
                ln for ln in best_score_lines
                if " best score: 65.67" in ln
            ]) == 1
