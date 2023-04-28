#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for the service to run the scripts locally.
"""
import os
import sys

import pytest
import pandas

from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.services.config_persistence import ConfigPersistenceService

# pylint: disable=redefined-outer-name
# -- Ignore pylint complaints about pytest references to
# `local_exec_service` fixture as both a function and a parameter.


@pytest.fixture
def local_exec_service() -> LocalExecService:
    """
    Test fixture for LocalExecService.
    """
    return LocalExecService(parent=ConfigPersistenceService())


def test_run_script(local_exec_service: LocalExecService) -> None:
    """
    Run a script locally and check the results.
    """
    # `echo` should work on all platforms
    (return_code, stdout, stderr) = local_exec_service.local_exec(["echo hello"])
    assert return_code == 0
    assert stdout.strip() == "hello"
    assert stderr.strip() == ""


def test_run_script_multiline(local_exec_service: LocalExecService) -> None:
    """
    Run a multiline script locally and check the results.
    """
    # `echo` should work on all platforms
    (return_code, stdout, stderr) = local_exec_service.local_exec([
        "echo hello",
        "echo world"
    ])
    assert return_code == 0
    assert stdout.strip().split() == ["hello", "world"]
    assert stderr.strip() == ""


def test_run_script_multiline_env(local_exec_service: LocalExecService) -> None:
    """
    Run a multiline script locally and pass the environment variables to it.
    """
    # `echo` should work on all platforms
    (return_code, stdout, stderr) = local_exec_service.local_exec([
        r"echo $var",  # Unix shell
        r"echo %var%"  # Windows cmd
    ], env={"var": "VALUE", "int_var": 10})
    assert return_code == 0
    if sys.platform == 'win32':
        assert stdout.strip().split() == ["$var", "VALUE"]
    else:
        assert stdout.strip().split() == ["VALUE", "%var%"]
    assert stderr.strip() == ""


def test_run_script_read_csv(local_exec_service: LocalExecService) -> None:
    """
    Run a script locally and read the resulting CSV file.
    """
    with local_exec_service.temp_dir_context() as temp_dir:

        (return_code, stdout, stderr) = local_exec_service.local_exec([
            "echo 'col1,col2'> output.csv",  # No space before '>' to make it work on Windows
            "echo '111,222' >> output.csv",
            "echo '333,444' >> output.csv",
        ], cwd=temp_dir)

        assert return_code == 0
        assert stdout.strip() == ""
        assert stderr.strip() == ""

        data = pandas.read_csv(os.path.join(temp_dir, "output.csv"))
        assert all(data.col1 == [111, 333])
        assert all(data.col2 == [222, 444])


def test_run_script_write_read_txt(local_exec_service: LocalExecService) -> None:
    """
    Write data a temp location and run a script that updates it there.
    """
    with local_exec_service.temp_dir_context() as temp_dir:

        input_file = "input.txt"
        with open(os.path.join(temp_dir, input_file), "wt", encoding="utf-8") as fh_input:
            fh_input.write("hello\n")

        (return_code, stdout, stderr) = local_exec_service.local_exec([
            f"echo 'world' >> {input_file}",
            f"echo 'test' >> {input_file}",
        ], cwd=temp_dir)

        assert return_code == 0
        assert stdout.strip() == ""
        assert stderr.strip() == ""

        with open(os.path.join(temp_dir, input_file), "rt", encoding="utf-8") as fh_input:
            assert fh_input.read().split() == ["hello", "world", "test"]


def test_run_script_fail(local_exec_service: LocalExecService) -> None:
    """
    Try to run a non-existent command.
    """
    (return_code, stdout, _stderr) = local_exec_service.local_exec(["foo_bar_baz hello"])
    assert return_code != 0
    assert stdout.strip() == ""
