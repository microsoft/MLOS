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

# pylint: disable=redefined-outer-name


@pytest.fixture
def root_path() -> str:
    """
    Root path of mlos_bench project.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


@pytest.fixture
def config_loader(root_path: str) -> ConfigPersistenceService:
    """
    Test fixture for ConfigPersistenceService.
    """
    return ConfigPersistenceService({
        "config_path": [
            f"{root_path}/mlos_bench/config",
            f"{root_path}/mlos_bench/examples",
        ]
    })


@pytest.fixture
def local_exec_service(config_loader: ConfigPersistenceService) -> LocalExecService:
    """
    Test fixture for LocalExecService.
    """
    return LocalExecService(parent=config_loader)


def test_launch_main_app(root_path: str,
                         config_loader: ConfigPersistenceService,
                         local_exec_service: LocalExecService) -> None:
    """
    Run mlos_bench command-line application with mock config and check the results in the log.
    """
    config_path = config_loader.resolve_path("mock-1shot.jsonc")
    assert os.path.exists(config_path)

    with local_exec_service.temp_dir_context() as temp_dir:

        log_path = os.path.join(temp_dir, "mock-1shot.log")
        (return_code, _stdout, _stderr) = local_exec_service.local_exec([
            f"./mlos_bench/mlos_bench/run.py --config '{config_path}' --log_file '{log_path}'"
        ], cwd=root_path)

        assert return_code == 0

        with open(log_path, "rt", encoding="utf-8") as fh_out:
            assert len([
                ln.strip() for ln in fh_out.readlines()
                if " INFO Env: Mock environment best score: 70.35" in ln
            ]) == 1
