"""
Unit tests for teh service to run the scripts locally.
"""

import pytest

from mlos_bench.environment import Status, LocalExecService, ConfigPersistenceService

# Ignore some pylint complaints about pytest references to `local_exec_service` as both a class and for the fixture parameters.
# pylint: disable=redefined-outer-name


@pytest.fixture
def local_exec_service() -> LocalExecService:
    """
    Test fixture for LocalExecService.
    """
    return LocalExecService(parent=ConfigPersistenceService())


def test_run_script(local_exec_service: LocalExecService):
    """
    Run a script locally and check the results.
    """
    # `echo` should work on all platforms
    (status, output) = local_exec_service.local_exec(["echo hello"])
    assert status == Status.SUCCEEDED
    assert output.strip() == "hello"


def test_run_script_multiline(local_exec_service: LocalExecService):
    """
    Run a script locally and check the results.
    """
    # `echo` should work on all platforms
    (status, output) = local_exec_service.local_exec([
        "echo hello",
        "echo world"
    ])
    assert status == Status.SUCCEEDED
    assert output.strip().split() == ["hello", "world"]


def test_run_script_csv(local_exec_service: LocalExecService):
    """
    Run a script locally and read the resulting CSV file.
    """
    # `echo` should work on all platforms
    (status, output) = local_exec_service.local_exec([
        "echo 'col1,col2'> output.csv",  # Hack: no space before '>' to make it work on Windows
        "echo '111,222' >> output.csv",
        "echo '333,444' >> output.csv",
        "cat output.csv",
    ], output_csv_file="output.csv")
    assert status == Status.SUCCEEDED
    assert all(output.col1 == [111, 333])
    assert all(output.col2 == [222, 444])


def test_run_script_fail(local_exec_service: LocalExecService):
    """
    Try to run a non-existent command.
    """
    (status, output) = local_exec_service.local_exec(["foo_bar_baz hello"])
    assert status == Status.FAILED
    assert output.strip() == ""
