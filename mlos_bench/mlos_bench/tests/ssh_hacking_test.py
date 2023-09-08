"""
test.py
"""

from asyncio import AbstractEventLoop, Lock as CoroutineLock
from concurrent.futures import Future
from threading import Thread, current_thread
from time import time
from typing import Dict, List, Optional, Tuple

import asyncio
import os

import logging

from asyncssh import SSHCompletedProcess, SSHClient, SSHClientConnection
import asyncssh

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


class SshCachedClient(asyncssh.SSHClient):
    """
    Wrapper around SSHClient to provide connection caching and reconnect logic.
    """
    _cache: Dict[str, Tuple[SSHClientConnection, SSHClient]] = {}
    _cache_lock = CoroutineLock()

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
    async def get_client_connection(connect_params: dict, i: int = -1) -> Tuple[SSHClientConnection, SSHClient]:
        """Gets a (possibly cached) client connection."""
        _LOG.warning("%s: %s", current_thread().name, "get_client_connection")
        _LOG.warning("%d: get_client_connection: %s", i, connect_params)
        start_time = time()
        async with SshCachedClient._cache_lock:
            assert SshCachedClient._cache_lock.locked()
            time_taken = time() - start_time
            _LOG.warning("%d: acquired cache lock in %f seconds", i, time_taken)
            connection_id = SshCachedClient.connection_id_from_params(connect_params)
            if connection_id not in SshCachedClient._cache:
                _LOG.warning("%d: establishing connection to %s", i, connection_id)
                connect_params.setdefault('env', {})
                connect_params['env']['CLIENT_ID'] = str(i)
                start_time = time()
                SshCachedClient._cache[connection_id] = await asyncssh.create_connection(SshCachedClient, **connect_params)
                time_taken = time() - start_time
                _LOG.warning("%d: connected to %s in %f seconds", i, connection_id, time_taken)
            else:
                _LOG.warning("%d: using cached connection %s", i, connection_id)
            return SshCachedClient._cache[connection_id]

    def connection_made(self, conn: SSHClientConnection) -> None:
        """Override hook provided by asyncssh.SSHClient."""
        _LOG.warning("%s: %s", current_thread().name, "connection_made")
        _LOG.warning("connection made by %s: %s", conn._options.env, conn)
        # FIXME: await SshCachedClient._cache_lock.acquire()
        # _LOG.warning("acquired lock")
        self._connection_id = SshCachedClient.connection_id(conn)
        _LOG.warning("caching connection %s: %s", self._connection_id, conn)
        SshCachedClient._cache[self._connection_id] = (conn, self)
        # FIXME: SshCachedClient._cache_lock.release()
        return super().connection_made(conn)

    async def _async_remove_cached_connection(self, connection_id: str) -> None:
        """Removes a cached connection."""
        _LOG.warning("removing cached connection %s", connection_id)
        async with self._cache_lock:
            assert self._cache_lock.locked()
            (connection, client) = SshCachedClient._cache.pop(connection_id, (None, None))
            assert self == client

    def connection_lost(self, exc: Optional[Exception]) -> None:
        _LOG.warning("%s: %s", current_thread().name, "connection_lost")
        if exc is None:
            _LOG.warning("Gracefully disconnected from %s: %s", self._connection_id, exc)
        else:
            _LOG.warning("Connection lost on %s: %s", self._connection_id, exc)
            # TODO: Reconnect?
        return super().connection_lost(exc)


CONNECT_PARAMS = {
    'host': 'host.docker.internal',
    'port': 2222,
    'known_hosts': None,
    'username': os.getenv('LOCAL_USER_NAME', os.getenv('USER', os.getenv('USERNAME', None))),
}

EVENT_LOOP = asyncio.new_event_loop()


async def remote_exec(connect_params: dict, cmd: str, i: int) -> SSHCompletedProcess:
    """Run a command on a remote host, connecting if necessary."""
    _LOG.warning("%d: remote_exec running in background thread %d", i, i)
    start_time = time()
    connection, _ = await SshCachedClient.get_client_connection(connect_params, i)
    time_taken = time() - start_time
    if i == 2 and False:
        connection.disconnect(code=-1, reason="disconnecting")
    _LOG.warning("%d: remote_exec got connection in %f seconds", i, time_taken)
    start_time = time()
    result = await connection.run(cmd, check=False)
    time_taken = time() - start_time
    _LOG.warning("%d: remote_exec got result from cmd '%s' in %f seconds", i, cmd, time_taken)
    return result


def background_event_loop_thread(event_loop: AbstractEventLoop) -> None:
    """Entry point for a background event loop thread."""
    _LOG.warning("Starting background event loop thread")
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()


def test_ssh() -> None:
    """test ssh async funcs"""

    # Start an event loop thread in the background.
    event_loop = asyncio.new_event_loop()
    event_loop_thread = Thread(target=background_event_loop_thread, args=(event_loop,), daemon=True)
    event_loop_thread.start()

    preconnect = False
    if preconnect:
        _LOG.warning("preconnecting")
        connect_future = asyncio.run_coroutine_threadsafe(SshCachedClient.get_client_connection(
            connect_params=CONNECT_PARAMS.copy(), i=-1), event_loop)
        connection, client = connect_future.result()
        _LOG.warning("connection: %s", connection)
        _LOG.warning("client: %s", client)

    MAX_CMDs = 4
    cmd_futures: List[Future[SSHCompletedProcess]] = []
    for i in range(0, MAX_CMDs):
        cmd = r'date +%s.%N; sleep 1; printenv'
        if i == 2:
            cmd = r'date +%s.%N; sleep .1; sudo -n pkill sshd'
        cmd_futures.append(
            asyncio.run_coroutine_threadsafe(
                remote_exec(
                    connect_params=CONNECT_PARAMS.copy(),
                    cmd=cmd,
                    i=i),
                event_loop))

    for i in range(0, MAX_CMDs):
        result = cmd_futures[i].result()
        _LOG.warning("%d: result[%s]:\n%s", i, result.returncode, result.stdout)

    # Submit a task to the event loop to stop itself.
    event_loop.call_soon_threadsafe(event_loop.stop)
    # Wait for the event loop thread to finish.
    event_loop_thread.join()

    print("Done")


if __name__ == "__main__":
    print(_LOG)
    main_start_time = time()
    test_ssh()
    main_time_taken = time() - main_start_time
    _LOG.warning("test_ssh took %f seconds", main_time_taken)
