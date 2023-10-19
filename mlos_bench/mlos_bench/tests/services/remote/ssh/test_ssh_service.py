#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_bench.services.remote.ssh.SshService base class.
"""

import asyncio
import gc
import time

from subprocess import run
from threading import Thread

import pytest
from pytest_lazyfixture import lazy_fixture

from mlos_bench.services.remote.ssh.ssh_service import SshService
from mlos_bench.services.remote.ssh.ssh_host_service import SshHostService
from mlos_bench.services.remote.ssh.ssh_fileshare import SshFileShareService

from mlos_bench.tests import requires_docker, requires_ssh, check_socket, resolve_host_name
from mlos_bench.tests.services.remote.ssh import SshTestServerInfo, ALT_TEST_SERVER_NAME, SSH_TEST_SERVER_NAME


@requires_docker
@requires_ssh
@pytest.mark.xdist_group("ssh_test_server")
@pytest.mark.parametrize(["ssh_test_server_info", "server_name"], [
    (lazy_fixture("ssh_test_server"), SSH_TEST_SERVER_NAME),
    (lazy_fixture("alt_test_server"), ALT_TEST_SERVER_NAME),
])
def test_ssh_service_test_infra(ssh_test_server_info: SshTestServerInfo,
                                server_name: str) -> None:
    """Check for the pytest-docker ssh test infra."""
    assert ssh_test_server_info.service_name == server_name

    ip_addr = resolve_host_name(ssh_test_server_info.hostname)
    assert ip_addr is not None

    local_port = ssh_test_server_info.get_port()
    assert check_socket(ip_addr, local_port)
    ssh_cmd = "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new " \
        + f"-l {ssh_test_server_info.username} -i {ssh_test_server_info.id_rsa_path} " \
        + f"-p {local_port} {ssh_test_server_info.hostname} hostname"
    cmd = run(ssh_cmd.split(),
              capture_output=True,
              text=True,
              check=True)
    assert cmd.stdout.strip() == server_name


@pytest.mark.xdist_group("ssh_test_server")
def test_ssh_service_background_thread() -> None:
    """Test the SSH service background thread setup/cleanup handling."""
    # pylint: disable=protected-access

    # Should start with no event loop thread.
    gc.collect()
    assert SshService._event_loop_thread is None

    # After we make an initial SshService instance, we should have a thread.
    ssh_host_service = SshHostService(config={}, global_config={}, parent=None)
    assert ssh_host_service
    assert isinstance(SshService._event_loop_thread, Thread)
    # Give the thread a chance to start.
    # Mostly important on the underpowered Windows CI machines.
    time.sleep(0.25)    # type: ignore[unreachable] # (false positive)
    assert SshService._event_loop_thread.is_alive()
    assert SshService._event_loop_thread_refcnt == 1
    assert SshService._event_loop_thread_ssh_client_cache is not None
    assert SshService._event_loop is not None
    assert SshService._event_loop.is_running()

    # But we should only get one thread.
    ssh_fileshare_service = SshFileShareService(config={}, global_config={}, parent=None)
    assert ssh_fileshare_service
    assert SshService._event_loop_thread_refcnt == 2
    assert SshService._event_loop_thread is ssh_host_service._event_loop_thread is ssh_fileshare_service._event_loop_thread
    assert SshService._event_loop is ssh_host_service._event_loop is ssh_fileshare_service._event_loop

    # And it should remain after we delete the first instance.
    # Note: since GC is not guaranteed, we need to provide a way to explicitly close an instance.
    ssh_host_service.close()
    # And that instance should be unusable after we explicitly close it.
    assert not ssh_host_service._enabled
    with pytest.raises(AssertionError):
        ssh_host_service._run_coroutine(asyncio.sleep(0.1))
    del ssh_host_service
    gc.collect()
    assert SshService._event_loop_thread_refcnt == 1
    assert SshService._event_loop_thread is not None
    assert SshService._event_loop_thread.is_alive()
    assert SshService._event_loop is not None
    assert SshService._event_loop.is_running()
    assert SshService._event_loop_thread_ssh_client_cache is not None

    # But not after we delete the remaining instances.
    ssh_fileshare_service.close()
    del ssh_fileshare_service
    gc.collect()
    assert SshService._event_loop_thread is None
    assert SshService._event_loop_thread_refcnt == 0
    assert SshService._event_loop is None
    assert SshService._event_loop_thread_ssh_client_cache is None


if __name__ == '__main__':
    # For debugging in Windows which has issues with pytest detection in vscode.
    pytest.main(["-n1", "--dist=no", "-k", "test_ssh_service_background_thread"])
