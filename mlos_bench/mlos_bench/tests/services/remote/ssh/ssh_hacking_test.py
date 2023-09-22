#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
test.py
"""

from asyncio import AbstractEventLoop, Event as CoroEvent, Lock as CoroLock
from concurrent.futures import Future
from distutils.util import strtobool    # pylint: disable=deprecated-module
from subprocess import run
from threading import Thread, current_thread
from time import time, sleep
from typing import Dict, Generator, List, Optional, Tuple, Union

import asyncio
import os

import logging

import pytest

from asyncssh import SSHCompletedProcess, SSHClient, SSHClientConnection, ProcessError, ConnectionLost, DisconnectError
import asyncssh

from mlos_bench.tests.services.remote.ssh import SshTestServerInfo, SSH_TEST_SERVER_NAME, SSH_TEST_SERVER_PORT


_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)

SCRIPT_DIR = os.path.dirname(__file__)


class SshClient(asyncssh.SSHClient):
    """
    Wrapper around SSHClient to help provide connection caching and reconnect logic.
    """

    _CONNECTION_PENDING = "INIT"
    _CONNECTION_LOST = "LOST"

    def __init__(self, *args: tuple, **kwargs: dict):
        self._connection_id: str = SshClient._CONNECTION_PENDING
        self._connection: Optional[SSHClientConnection] = None
        self._conn_event: CoroEvent = CoroEvent()
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return self._connection_id

    def __repr__(self) -> str:
        return self._connection_id

    @staticmethod
    def id_from_connection(connection: SSHClientConnection) -> str:
        """Gets a unique id repr for the connection."""
        return f"{connection._username}@{connection._host}:{connection._port}"    # pylint: disable=protected-access

    @staticmethod
    def id_from_params(connect_params: dict) -> str:
        """Gets a unique id repr for the connection."""
        return f"{connect_params['username']}@{connect_params['host']}:{connect_params['port']}"

    def connection_made(self, conn: SSHClientConnection) -> None:
        """
        Override hook provided by asyncssh.SSHClient.

        Changes the connection_id from _CONNECTION_PENDING to a unique id repr.
        """
        self._conn_event.clear()
        _LOG.warning("%s: Connection made by %s: %s", current_thread().name, conn._options.env, conn) \
            # pylint: disable=protected-access
        self._connection_id = SshClient.id_from_connection(conn)
        self._connection = conn
        self._conn_event.set()
        return super().connection_made(conn)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self._conn_event.clear()
        _LOG.warning("%s: %s", current_thread().name, "connection_lost")
        if exc is None:
            _LOG.warning("%s: Gracefully disconnected from %s: %s", current_thread().name, self._connection_id, exc)
        else:
            _LOG.warning("%s: Connection lost on %s: %s", current_thread().name, self._connection_id, exc)
        self._connection_id = SshClient._CONNECTION_LOST
        self._connection = None
        self._conn_event.set()
        return super().connection_lost(exc)

    async def connection(self) -> Optional[SSHClientConnection]:
        """
        Waits for the ssh connection.
        """
        _LOG.warning("%s: Waiting for connection to be available.", current_thread().name)
        start_time = time()
        await self._conn_event.wait()
        time_taken = time() - start_time
        _LOG.warning("%s: Connection available after waiting for %f seconds: %s",
                     current_thread().name, time_taken, self._connection_id)
        return self._connection


class SshClientCache:
    """
    Manages a cache of SshClient connections.
    One per event loop thread.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[SSHClientConnection, SshClient]] = {}
        self._cache_lock = CoroLock()

    def __str__(self) -> str:
        return str(self._cache)

    async def get_client_connection(self,
                                    connect_params: dict,
                                    i: int = -1) -> Tuple[SSHClientConnection, SshClient]:
        """
        Gets a (possibly cached) client connection.

        Parameters
        ----------
        connect_params: dict
            Parameters to pass to asyncssh.create_connection.
        i: int
            Client id.

        Returns
        -------
        Tuple[SshClient]
            A tuple of (SshClient, SSHClientConnection).
        """
        _LOG.warning("%s: %d: get_client_connection: %s", current_thread().name, i, connect_params)
        start_time = time()
        async with self._cache_lock:
            time_taken = time() - start_time
            _LOG.warning("%s: %d: acquired cache lock in %f seconds", current_thread().name, i, time_taken)
            connection_id = SshClient.id_from_params(connect_params)
            client: Union[None, SshClient, SSHClient]
            _, client = self._cache.get(connection_id, (None, None))
            if client:
                _LOG.warning("%s: %d: Checking cached client %s", current_thread().name, i, connection_id)
                start_time = time()
                connection = await client.connection()
                time_taken = time() - start_time
                if not connection:
                    _LOG.warning("%s: %d: Removing stale client connection %s from cache.", current_thread().name, i, connection_id)
                    self._cache.pop(connection_id)
                    # Try to reconnect next.
                else:
                    _LOG.warning("%s: %d: Using cached client %s", current_thread().name, i, connection_id)
            if connection_id not in self._cache:
                _LOG.warning("%s: %d: Establishing client connection to %s", current_thread().name, i, connection_id)
                # for debugging/hacking/testing - to tell who made the connection originally:
                connect_params.setdefault('env', {})
                connect_params['env']['CLIENT_ID'] = str(i)

                start_time = time()
                connection, client = await asyncssh.create_connection(SshClient, **connect_params)
                assert isinstance(client, SshClient)
                self._cache[connection_id] = (connection, client)
                time_taken = time() - start_time
                _LOG.warning("%s: %d: Created connection to %s in %f seconds", current_thread().name, i, connection_id, time_taken)
            _LOG.warning("%s: %d: current cache: %s", current_thread().name, i, str(self._cache))
            return self._cache[connection_id]


async def remote_exec(ssh_client_cache: SshClientCache, connect_params: dict, cmd: str, i: int) -> SSHCompletedProcess:
    """Run a command on a remote host, connecting if necessary."""
    _LOG.warning("%d: remote_exec running in background thread %d", i, i)
    start_time = time()
    connection, _ = await ssh_client_cache.get_client_connection(connect_params, i)
    time_taken = time() - start_time
    test_disconnect = False
    if i == 2 and test_disconnect:
        connection.disconnect(code=-1, reason="disconnecting")
    _LOG.warning("%s: %d: remote_exec got connection in %f seconds", current_thread().name, i, time_taken)
    start_time = time()
    try:
        result = await connection.run(cmd, check=True)
        if result.returncode != 0 or result.exit_status != 0:
            raise RuntimeError(f"remote_exec got non-zero return code: {result.returncode} {result.exit_status}: {result}")
    except (ConnectionLost, DisconnectError, ProcessError, RuntimeError) as exc:
        _LOG.warning("%s: %d: remote_exec got exception: %s", current_thread().name, i, exc)
    time_taken = time() - start_time
    _LOG.warning("%s: %d: remote_exec got result from cmd '%s' in %f seconds", current_thread().name, i, cmd, time_taken)
    return result


def background_event_loop_thread(event_loop: AbstractEventLoop) -> None:
    """Entry point for a background event loop thread."""
    _LOG.warning("Starting background event loop thread")
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()


def start_ssh_test_server() -> SshTestServerInfo:
    """Starts an ssh server in a docker container."""
    run("./up.sh", cwd=SCRIPT_DIR, check=True)
    cmd_result = run(f"docker compose -p 'mlos_bench-test-manual' port {SSH_TEST_SERVER_NAME} {SSH_TEST_SERVER_PORT}",
                     check=True, shell=True, capture_output=True)
    host, port = cmd_result.stdout.decode().strip().split(":")
    assert host == '0.0.0.0'
    return SshTestServerInfo(
        hostname='host.docker.internal',
        port=int(port),
        username='root',
        id_rsa_path=os.path.join(SCRIPT_DIR, 'id_rsa'),
    )


@pytest.fixture(scope="module")
def ssh_test_server() -> Generator[SshTestServerInfo, None, None]:
    """Starts an ssh server in a docker container as a pytest fixture."""
    ssh_test_server_info = start_ssh_test_server()
    yield ssh_test_server_info
    # Down the server after the test.
    # run("./down.sh", cwd=SCRIPT_DIR, check=True)


# NOTE: Set SSH_HACKING_TEST=true to enable this test.
# e.g., in the .env file in the devcontainer.
@pytest.mark.skipif(not strtobool(os.getenv("SSH_HACKING_TEST", "false")), reason="SSH_HACKING_TEST not enabled")
def test_ssh_hacking(ssh_test_server: SshTestServerInfo) -> None:  # pylint: disable=redefined-outer-name
    """test ssh async funcs"""

    # Start an event loop thread in the background.
    event_loop = asyncio.new_event_loop()
    event_loop_thread = Thread(target=background_event_loop_thread, args=(event_loop,), daemon=True)
    event_loop_thread.start()
    event_loop_thread_ssh_client_cache = SshClientCache()

    connect_params = {
        'host': ssh_test_server.hostname,
        'port': ssh_test_server.port,
        'username': ssh_test_server.username,
        'known_hosts': None,
        'client_keys': [ssh_test_server.id_rsa_path],
    }

    preconnect = False
    if preconnect:
        _LOG.warning("preconnecting")
        connect_future = asyncio.run_coroutine_threadsafe(event_loop_thread_ssh_client_cache.get_client_connection(
            connect_params=connect_params.copy(), i=-1), event_loop)
        connection, client = connect_future.result()
        _LOG.warning("connection: %s", connection)
        _LOG.warning("client: %s", client)

    max_cmds = 8
    cmd_futures: List[Future[SSHCompletedProcess]] = []
    for i in range(0, max_cmds):
        cmd = r'date +%s.%N; sleep 1; printenv'
        test_ssh_disconnected = True
        if i == 2 and test_ssh_disconnected:
            cmd = r'date +%s.%N; sleep .1; sudo -n pkill sshd'
        if i == 4 and test_ssh_disconnected:
            sleep(.5)
            run("./up.sh", cwd=SCRIPT_DIR, check=True)
        cmd_futures.append(
            asyncio.run_coroutine_threadsafe(
                remote_exec(
                    event_loop_thread_ssh_client_cache,
                    connect_params=connect_params.copy(),
                    cmd=cmd,
                    i=i),
                event_loop))

    for i in range(0, max_cmds):
        result = cmd_futures[i].result()
        _LOG.warning("%d: result[%s, %s]:\nstdout:\n%s\nstderr:\n%s",
                     i, result.returncode, result.exit_status, result.stdout, result.stderr)

    # Submit a task to the event loop to stop itself.
    event_loop.call_soon_threadsafe(event_loop.stop)
    # Wait for the event loop thread to finish.
    event_loop_thread.join()

    print("Done")


if __name__ == "__main__":
    print(_LOG)
    main_start_time = time()
    main_ssh_test_server_info = start_ssh_test_server()
    main_time_taken = time() - main_start_time
    _LOG.warning("start_ssh_test_server() took %f seconds", main_time_taken)

    main_start_time = time()
    test_ssh_hacking(main_ssh_test_server_info)
    main_time_taken = time() - main_start_time

    _LOG.warning("test_ssh_hacking() took %f seconds", main_time_taken)
