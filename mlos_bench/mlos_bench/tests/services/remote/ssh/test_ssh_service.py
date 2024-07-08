#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for mlos_bench.services.remote.ssh.SshService base class."""

import asyncio
import time
from importlib.metadata import PackageNotFoundError, version
from subprocess import run
from threading import Thread

import pytest
from pytest_lazy_fixtures.lazy_fixture import lf as lazy_fixture

from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService
from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_service import SshService
from mlos_bench.tests import (
    check_socket,
    requires_docker,
    requires_ssh,
    resolve_host_name,
)
from mlos_bench.tests.services.remote.ssh import (
    ALT_TEST_SERVER_NAME,
    SSH_TEST_SERVER_NAME,
    SshTestServerInfo,
)

if version("pytest") >= "8.0.0":
    try:
        # We replaced pytest-lazy-fixture with pytest-lazy-fixtures:
        # https://github.com/TvoroG/pytest-lazy-fixture/issues/65
        if version("pytest-lazy-fixture"):
            raise UserWarning(
                "pytest-lazy-fixture conflicts with pytest>=8.0.0.  Please remove it."
            )
    except PackageNotFoundError:
        # OK: pytest-lazy-fixture not installed
        pass


@requires_docker
@requires_ssh
@pytest.mark.parametrize(
    ["ssh_test_server_info", "server_name"],
    [
        (lazy_fixture("ssh_test_server"), SSH_TEST_SERVER_NAME),
        (lazy_fixture("alt_test_server"), ALT_TEST_SERVER_NAME),
    ],
)
def test_ssh_service_test_infra(ssh_test_server_info: SshTestServerInfo, server_name: str) -> None:
    """Check for the pytest-docker ssh test infra."""
    assert ssh_test_server_info.service_name == server_name

    ip_addr = resolve_host_name(ssh_test_server_info.hostname)
    assert ip_addr is not None

    local_port = ssh_test_server_info.get_port()
    assert check_socket(ip_addr, local_port)
    ssh_cmd = (
        "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "
        + f"-l {ssh_test_server_info.username} -i {ssh_test_server_info.id_rsa_path} "
        + f"-p {local_port} {ssh_test_server_info.hostname} hostname"
    )
    cmd = run(ssh_cmd.split(), capture_output=True, text=True, check=True)
    assert cmd.stdout.strip() == server_name


@pytest.mark.filterwarnings(
    "ignore:.*(coroutine 'sleep' was never awaited).*:RuntimeWarning:.*event_loop_context_test.*:0"
)
def test_ssh_service_context_handler() -> None:
    """
    Test the SSH service context manager handling.

    See Also: test_event_loop_context
    """
    # pylint: disable=protected-access

    # Should start with no event loop thread.
    assert SshService._EVENT_LOOP_CONTEXT._event_loop_thread is None

    # The background thread should only be created upon context entry.
    ssh_host_service = SshHostService(config={}, global_config={}, parent=None)
    assert ssh_host_service
    assert not ssh_host_service._in_context
    assert ssh_host_service._EVENT_LOOP_CONTEXT._event_loop_thread is None

    # After we enter the SshService instance context, we should have a background thread.
    with ssh_host_service:
        assert ssh_host_service._in_context
        assert (  # type: ignore[unreachable]
            isinstance(SshService._EVENT_LOOP_CONTEXT._event_loop_thread, Thread)
        )
        # Give the thread a chance to start.
        # Mostly important on the underpowered Windows CI machines.
        time.sleep(0.25)
        assert SshService._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE is not None

        ssh_fileshare_service = SshFileShareService(config={}, global_config={}, parent=None)
        assert ssh_fileshare_service
        assert not ssh_fileshare_service._in_context

        with ssh_fileshare_service:
            assert ssh_fileshare_service._in_context
            assert ssh_host_service._in_context
            assert (
                SshService._EVENT_LOOP_CONTEXT._event_loop_thread
                is ssh_host_service._EVENT_LOOP_CONTEXT._event_loop_thread
                is ssh_fileshare_service._EVENT_LOOP_CONTEXT._event_loop_thread
            )
            assert (
                SshService._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE
                is ssh_host_service._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE
                is ssh_fileshare_service._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE
            )

        assert not ssh_fileshare_service._in_context
        # And that instance should be unusable after we are outside the context.
        with pytest.raises(
            AssertionError
        ):  # , pytest.warns(RuntimeWarning, match=r".*coroutine 'sleep' was never awaited"):
            future = ssh_fileshare_service._run_coroutine(asyncio.sleep(0.1, result="foo"))
            raise ValueError(f"Future should not have been available to wait on {future.result()}")

        # The background thread should remain running since we have another context still open.
        assert isinstance(SshService._EVENT_LOOP_CONTEXT._event_loop_thread, Thread)
        assert SshService._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE is not None


if __name__ == "__main__":
    # For debugging in Windows which has issues with pytest detection in vscode.
    pytest.main(["-n1", "--dist=no", "-k", "test_ssh_service_background_thread"])
