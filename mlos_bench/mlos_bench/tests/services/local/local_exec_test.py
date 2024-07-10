#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for the service to run the scripts locally."""
import sys
import tempfile

import pandas
import pytest

from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService, split_cmdline
from mlos_bench.util import path_join

# pylint: disable=redefined-outer-name
# -- Ignore pylint complaints about pytest references to
# `local_exec_service` fixture as both a function and a parameter.


def test_split_cmdline() -> None:
    """Test splitting a commandline into subcommands."""
    cmdline = (
        ". env.sh && (echo hello && echo world | tee > /tmp/test || echo foo && echo $var; true)"
    )
    assert list(split_cmdline(cmdline)) == [
        [".", "env.sh"],
        ["&&"],
        ["("],
        ["echo", "hello"],
        ["&&"],
        ["echo", "world"],
        ["|"],
        ["tee"],
        [">"],
        ["/tmp/test"],
        ["||"],
        ["echo", "foo"],
        ["&&"],
        ["echo", "$var"],
        [";"],
        ["true"],
        [")"],
    ]


@pytest.fixture
def local_exec_service() -> LocalExecService:
    """Test fixture for LocalExecService."""
    config = {
        "abort_on_error": True,
    }
    return LocalExecService(config, parent=ConfigPersistenceService())


def test_resolve_script(local_exec_service: LocalExecService) -> None:
    """Test local script resolution logic with complex subcommand names."""
    script = "os/linux/runtime/scripts/local/generate_kernel_config_script.py"
    script_abspath = local_exec_service.config_loader_service.resolve_path(script)
    orig_cmdline = f". env.sh && {script} --input foo"
    expected_cmdline = f". env.sh && {script_abspath} --input foo"
    subcmds_tokens = split_cmdline(orig_cmdline)
    # pylint: disable=protected-access
    subcmds_tokens = [
        local_exec_service._resolve_cmdline_script_path(subcmd_tokens)
        for subcmd_tokens in subcmds_tokens
    ]
    cmdline_tokens = [token for subcmd_tokens in subcmds_tokens for token in subcmd_tokens]
    expanded_cmdline = " ".join(cmdline_tokens)
    assert expanded_cmdline == expected_cmdline


def test_run_script(local_exec_service: LocalExecService) -> None:
    """Run a script locally and check the results."""
    # `echo` should work on all platforms
    (return_code, stdout, stderr) = local_exec_service.local_exec(["echo hello"])
    assert return_code == 0
    assert stdout.strip() == "hello"
    assert stderr.strip() == ""


def test_run_script_multiline(local_exec_service: LocalExecService) -> None:
    """Run a multiline script locally and check the results."""
    # `echo` should work on all platforms
    (return_code, stdout, stderr) = local_exec_service.local_exec(["echo hello", "echo world"])
    assert return_code == 0
    assert stdout.strip().split() == ["hello", "world"]
    assert stderr.strip() == ""


def test_run_script_multiline_env(local_exec_service: LocalExecService) -> None:
    """Run a multiline script locally and pass the environment variables to it."""
    # `echo` should work on all platforms
    (return_code, stdout, stderr) = local_exec_service.local_exec(
        [r"echo $var", r"echo %var%"],  # Unix shell  # Windows cmd
        env={"var": "VALUE", "int_var": 10},
    )
    assert return_code == 0
    if sys.platform == "win32":
        assert stdout.strip().split() == ["$var", "VALUE"]
    else:
        assert stdout.strip().split() == ["VALUE", "%var%"]
    assert stderr.strip() == ""


def test_run_script_read_csv(local_exec_service: LocalExecService) -> None:
    """Run a script locally and read the resulting CSV file."""
    with local_exec_service.temp_dir_context() as temp_dir:

        (return_code, stdout, stderr) = local_exec_service.local_exec(
            [
                "echo 'col1,col2'> output.csv",  # No space before '>' to make it work on Windows
                "echo '111,222' >> output.csv",
                "echo '333,444' >> output.csv",
            ],
            cwd=temp_dir,
        )

        assert return_code == 0
        assert stdout.strip() == ""
        assert stderr.strip() == ""

        data = pandas.read_csv(path_join(temp_dir, "output.csv"))
        if sys.platform == "win32":
            # Workaround for Python's subprocess module on Windows adding a
            # space inbetween the col1,col2 arg and the redirect symbol which
            # cmd poorly interprets as being part of the original string arg.
            # Without this, we get "col2 " as the second column name.
            data.rename(str.rstrip, axis="columns", inplace=True)
        assert all(data.col1 == [111, 333])
        assert all(data.col2 == [222, 444])


def test_run_script_write_read_txt(local_exec_service: LocalExecService) -> None:
    """Write data a temp location and run a script that updates it there."""
    with local_exec_service.temp_dir_context() as temp_dir:

        input_file = "input.txt"
        with open(path_join(temp_dir, input_file), "wt", encoding="utf-8") as fh_input:
            fh_input.write("hello\n")

        (return_code, stdout, stderr) = local_exec_service.local_exec(
            [
                f"echo 'world' >> {input_file}",
                f"echo 'test' >> {input_file}",
            ],
            cwd=temp_dir,
        )

        assert return_code == 0
        assert stdout.strip() == ""
        assert stderr.strip() == ""

        with open(path_join(temp_dir, input_file), "rt", encoding="utf-8") as fh_input:
            assert fh_input.read().split() == ["hello", "world", "test"]


def test_run_script_fail(local_exec_service: LocalExecService) -> None:
    """Try to run a non-existent command."""
    (return_code, stdout, _stderr) = local_exec_service.local_exec(["foo_bar_baz hello"])
    assert return_code != 0
    assert stdout.strip() == ""


def test_run_script_middle_fail_abort(local_exec_service: LocalExecService) -> None:
    """Try to run a series of commands, one of which fails, and abort early."""
    (return_code, stdout, _stderr) = local_exec_service.local_exec(
        [
            "echo hello",
            "cmd /c 'exit 1'" if sys.platform == "win32" else "false",
            "echo world",
        ]
    )
    assert return_code != 0
    assert stdout.strip() == "hello"


def test_run_script_middle_fail_pass(local_exec_service: LocalExecService) -> None:
    """Try to run a series of commands, one of which fails, but let it pass."""
    local_exec_service.abort_on_error = False
    (return_code, stdout, _stderr) = local_exec_service.local_exec(
        [
            "echo hello",
            "cmd /c 'exit 1'" if sys.platform == "win32" else "false",
            "echo world",
        ]
    )
    assert return_code == 0
    assert stdout.splitlines() == [
        "hello",
        "world",
    ]


def test_temp_dir_path_expansion() -> None:
    """Test that we can control the temp_dir path using globals expansion."""
    # Create a temp dir for the test.
    # Normally this would be a real path set on the CLI or in a global config,
    # but for test purposes we still want it to be dynamic and cleaned up after
    # the fact.
    with tempfile.TemporaryDirectory() as temp_dir:
        global_config = {
            "workdir": temp_dir,  # e.g., "." or "/tmp/mlos_bench"
        }
        config = {
            # The temp_dir for the LocalExecService should get expanded via workdir global config.
            "temp_dir": "$workdir/temp",
        }
        local_exec_service = LocalExecService(
            config, global_config, parent=ConfigPersistenceService()
        )
        # pylint: disable=protected-access
        assert isinstance(local_exec_service._temp_dir, str)
        assert path_join(local_exec_service._temp_dir, abs_path=True) == path_join(
            temp_dir,
            "temp",
            abs_path=True,
        )
