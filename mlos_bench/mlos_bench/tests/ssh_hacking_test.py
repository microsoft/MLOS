"""
test.py
"""

from asyncio import AbstractEventLoop, Task
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Thread, RLock, current_thread
from typing import Any, Dict, Coroutine, List, Optional, Tuple

import asyncio
import os

import logging

from asyncssh import SSHCompletedProcess, SSHClient, SSHClientConnection
import asyncssh

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


async def ssh_rexec(host: str, port: int, username: Optional[str], cmd: str) -> SSHCompletedProcess:
    """Start an SSH command asynchronously and wait for the result"""
    connect_kwargs = {
        'host': host,
        'port': port,
        'known_hosts': None,
    }
    if username:
        connect_kwargs['username'] = username
    async with asyncssh.connect(**connect_kwargs) as conn:
        return await conn.run(cmd)


class SshCachedClient(asyncssh.SSHClient):
    """
    Wrapper around SSHClient to provide connection caching and reconnect logic.
    """
    _cache: Dict[str, Tuple[SSHClientConnection, SSHClient]] = {}
    _cache_lock = RLock()

    def __init__(self, *args: tuple, **kwargs: dict):
        self._connection_id: Optional[str] = None
        super().__init__(*args, **kwargs)

    @staticmethod
    def connection_id(connection: SSHClientConnection) -> str:
        """Gets a unique id repr for the connection."""
        # TODO: Check that these work.
        return f"{connection.get_extra_info('username')}@{connection.get_extra_info('host')}:{connection.get_extra_info('port')}"

    @staticmethod
    def connection_id_from_params(connect_params: dict) -> str:
        """Gets a unique id repr for the connection."""
        return f"{connect_params['username']}@{connect_params['host']}:{connect_params['port']}"

    @staticmethod
    def get_client_connection(connect_params: dict, i: int = -1) -> Tuple[SSHClientConnection, SSHClient]:
        """Gets a (possibly cached) client connection."""
        _LOG.warning("%d: get_client_connection: %s", i, connect_params)
        with SshCachedClient._cache_lock:
            _LOG.warning("%d: acquired cache lock", i)
            connection_id = SshCachedClient.connection_id_from_params(connect_params)
            if connection_id not in SshCachedClient._cache:
                _LOG.warning("%d: establishing connection to %s", i, connection_id)
                connect_params.setdefault('env', {})
                connect_params['env']['CLIENT_ID'] = str(i)
                SshCachedClient._cache[connection_id] = asyncio.run(asyncssh.create_connection(SshCachedClient, **connect_params))
            else:
                _LOG.warning("%d: using cached connection %s", i, connection_id)
            return SshCachedClient._cache[connection_id]

    def connection_made(self, conn: SSHClientConnection) -> None:
        """Override hook provided by asyncssh.SSHClient."""
        _LOG.warning("connection made by %s: %s", conn._options.env, conn)
        with SshCachedClient._cache_lock:
            _LOG.warning("acquired lock")
            self._connection_id = SshCachedClient.connection_id(conn)
            _LOG.warning("cached connection %s: %s", self._connection_id, conn)
            SshCachedClient._cache[self._connection_id] = (conn, self)
        return super().connection_made(conn)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if exc is None:
            _LOG.warning("Gracefully disconnected from %s: %s", self._connection_id, exc)
        else:
            _LOG.warning("Connection lost on %s: %s", self._connection_id, exc)
            with SshCachedClient._cache_lock:
                # Remove the connection from the cache.
                (connection, client) = SshCachedClient._cache.pop(str(self._connection_id), (None, None))
                assert self == client
                # TODO: Reconnect?
        return super().connection_lost(exc)


CONNECT_PARAMS = {
    'host': 'host.docker.internal',
    'port': 2222,
    'known_hosts': None,
    'username': os.getenv('LOCAL_USER_NAME', os.getenv('USER', os.getenv('USERNAME', None))),
}

EVENT_LOOP = asyncio.new_event_loop()


def remote_exec(connect_params: dict, cmd: str, i: int) -> SSHCompletedProcess:
    _LOG.warning("remote_exec running in background thread %d", i)
    connection, _ = SshCachedClient.get_client_connection(connect_params, i)
    _LOG.warning("remote_exec got connection %s", connection)
    result = asyncio.run(connection.run(cmd, check=True))
    _LOG.warning("remote_exec got result %s", result)
    return result


def test_ssh() -> None:
    """test ssh async funcs"""
    # Dev note: submitting things to a loop on its own does nothing - we need to run the loop.

    thread_pool_executor = ThreadPoolExecutor(max_workers=3)

    futures: List[Future[SSHCompletedProcess]] = []

    # connect_future = event_loop.run_in_executor(thread_pool_executor, SshCachedClient.get_client_connection, connect_params)
    # connection, client = connect_future.result()

    MAX_CMDs = 4
    for i in range(0, MAX_CMDs):
        future = thread_pool_executor.submit(remote_exec, connect_params=CONNECT_PARAMS.copy(), cmd='sleep 1; printenv', i=i)
        futures.append(future)
    for i in range(0, MAX_CMDs):
        future = futures[i]
        result = future.result()
        _LOG.warning("%d: result:\n%s", i, result.stdout)
    thread_pool_executor.shutdown()
    print("Done")


if __name__ == "__main__":
    print(_LOG)
    test_ssh()
