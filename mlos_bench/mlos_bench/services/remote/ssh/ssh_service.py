#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection functions for interacting with SSH servers as file shares.
"""

from abc import ABCMeta
from asyncio import Event as CoroEvent, Lock as CoroLock
from warnings import warn
from types import TracebackType
from typing import Any, Callable, Coroutine, Dict, List, Literal, Optional, Tuple, Type, Union
from threading import current_thread

import logging
import os

import asyncssh
from asyncssh.connection import SSHClientConnection

from mlos_bench.services.base_service import Service
from mlos_bench.event_loop_context import EventLoopContext, CoroReturnType, FutureReturnType

_LOG = logging.getLogger(__name__)


class SshClient(asyncssh.SSHClient):
    """
    Wrapper around SSHClient to help provide connection caching and reconnect logic.

    Used by the SshService to try and maintain a single connection to hosts,
    handle reconnects if possible, and use that to run commands rather than
    reconnect for each command.
    """

    _CONNECTION_PENDING = 'INIT'
    _CONNECTION_LOST = 'LOST'

    def __init__(self, *args: tuple, **kwargs: dict):
        self._connection_id: str = SshClient._CONNECTION_PENDING
        self._connection: Optional[SSHClientConnection] = None
        self._conn_event: CoroEvent = CoroEvent()
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return self._connection_id

    @staticmethod
    def id_from_connection(connection: SSHClientConnection) -> str:
        """Gets a unique id repr for the connection."""
        return f"{connection._username}@{connection._host}:{connection._port}"    # pylint: disable=protected-access

    @staticmethod
    def id_from_params(connect_params: dict) -> str:
        """Gets a unique id repr for the connection."""
        return f"{connect_params.get('username')}@{connect_params['host']}:{connect_params.get('port')}"

    def connection_made(self, conn: SSHClientConnection) -> None:
        """
        Override hook provided by asyncssh.SSHClient.

        Changes the connection_id from _CONNECTION_PENDING to a unique id repr.
        """
        self._conn_event.clear()
        _LOG.debug("%s: Connection made by %s: %s", current_thread().name, conn._options.env, conn) \
            # pylint: disable=protected-access
        self._connection_id = SshClient.id_from_connection(conn)
        self._connection = conn
        self._conn_event.set()
        return super().connection_made(conn)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self._conn_event.clear()
        _LOG.debug("%s: %s", current_thread().name, "connection_lost")
        if exc is None:
            _LOG.debug("%s: gracefully disconnected ssh from %s: %s", current_thread().name, self._connection_id, exc)
        else:
            _LOG.debug("%s: ssh connection lost on %s: %s", current_thread().name, self._connection_id, exc)
        self._connection_id = SshClient._CONNECTION_LOST
        self._connection = None
        self._conn_event.set()
        return super().connection_lost(exc)

    async def connection(self) -> Optional[SSHClientConnection]:
        """
        Waits for and returns the SSHClientConnection to be established or lost.
        """
        _LOG.debug("%s: Waiting for connection to be available.", current_thread().name)
        await self._conn_event.wait()
        _LOG.debug("%s: Connection available for %s", current_thread().name, self._connection_id)
        return self._connection


class SshClientCache:
    """
    Manages a cache of SshClient connections.
    Note: Only one per event loop thread supported.
    See additional details in SshService comments.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[SSHClientConnection, SshClient]] = {}
        self._cache_lock = CoroLock()
        self._refcnt: int = 0

    def __str__(self) -> str:
        return str(self._cache)

    def __len__(self) -> int:
        return len(self._cache)

    def enter(self) -> None:
        """
        Manages the cache lifecycle with reference counting.
        To be used in the __enter__ method of a caller's context manager.
        """
        self._refcnt += 1

    def exit(self) -> None:
        """
        Manages the cache lifecycle with reference counting.
        To be used in the __exit__ method of a caller's context manager.
        """
        self._refcnt -= 1
        if self._refcnt <= 0:
            self.cleanup()
            if self._cache_lock.locked():
                warn(RuntimeWarning("SshClientCache lock was still held on exit."))
                self._cache_lock.release()

    async def get_client_connection(self, connect_params: dict) -> Tuple[SSHClientConnection, SshClient]:
        """
        Gets a (possibly cached) client connection.

        Parameters
        ----------
        connect_params: dict
            Parameters to pass to asyncssh.create_connection.

        Returns
        -------
        Tuple[SSHClientConnection, SshClient]
            A tuple of (SSHClientConnection, SshClient).
        """
        _LOG.debug("%s: get_client_connection: %s", current_thread().name, connect_params)
        async with self._cache_lock:
            connection_id = SshClient.id_from_params(connect_params)
            client: Union[None, SshClient, asyncssh.SSHClient]
            _, client = self._cache.get(connection_id, (None, None))
            if client:
                _LOG.debug("%s: Checking cached client %s", current_thread().name, connection_id)
                connection = await client.connection()
                if not connection:
                    _LOG.debug("%s: Removing stale client connection %s from cache.", current_thread().name, connection_id)
                    self._cache.pop(connection_id)
                    # Try to reconnect next.
                else:
                    _LOG.debug("%s: Using cached client %s", current_thread().name, connection_id)
            if connection_id not in self._cache:
                _LOG.debug("%s: Establishing client connection to %s", current_thread().name, connection_id)
                connection, client = await asyncssh.create_connection(SshClient, **connect_params)
                assert isinstance(client, SshClient)
                self._cache[connection_id] = (connection, client)
                _LOG.debug("%s: Created connection to %s.", current_thread().name, connection_id)
            return self._cache[connection_id]

    def cleanup(self) -> None:
        """
        Closes all cached connections.
        """
        for (connection, _) in self._cache.values():
            connection.close()
        self._cache = {}


class SshService(Service, metaclass=ABCMeta):
    """
    Base class for SSH services.
    """

    # AsyncSSH requires an asyncio event loop to be running to work.
    # However, running that event loop blocks the main thread.
    # To avoid having to change our entire API to use async/await, all the way
    # up the stack, we run the event loop that runs any async code in a
    # background thread and submit async code to it using
    # asyncio.run_coroutine_threadsafe, interacting with Futures after that.
    # This is a bit of a hack, but it works for now.
    #
    # The event loop is created on demand and shared across all SshService
    # instances, hence we need to lock it when doing the creation/cleanup,
    # or later, during context enter and exit.
    #
    # We ran tests to ensure that multiple requests can still be executing
    # concurrently inside that event loop so there should be no practical
    # performance loss for our initial cases even with just single background
    # thread running the event loop.
    #
    # Note: the tests were run to confirm that this works with two threads.
    # Using a larger thread pool requires a bit more work since asyncssh
    # requires that run() requests are submitted to the same event loop handler
    # that the connection was made on.
    # In that case, each background thread should get its own SshClientCache.

    # Maintain one just one event loop thread for all SshService instances.
    # But only keep it running while they are within a context.
    _EVENT_LOOP_CONTEXT = EventLoopContext()
    _EVENT_LOOP_THREAD_SSH_CLIENT_CACHE = SshClientCache()

    _REQUEST_TIMEOUT: Optional[float] = None  # seconds

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None,
                 methods: Union[Dict[str, Callable], List[Callable], None] = None):
        super().__init__(config, global_config, parent, methods)

        # Make sure that the value we allow overriding on a per-connection
        # basis are present in the config so merge_parameters can do its thing.
        self.config.setdefault('ssh_port', None)
        assert isinstance(self.config['ssh_port'], (int, type(None)))
        self.config.setdefault('ssh_username', None)
        assert isinstance(self.config['ssh_username'], (str, type(None)))
        self.config.setdefault('ssh_priv_key_path', None)
        assert isinstance(self.config['ssh_priv_key_path'], (str, type(None)))

        # None can be used to disable the request timeout.
        self._request_timeout = self.config.get("ssh_request_timeout", self._REQUEST_TIMEOUT)
        self._request_timeout = float(self._request_timeout) if self._request_timeout is not None else None

        # Prep an initial connect_params.
        self._connect_params: dict = {
            # In general scripted commands shouldn't need a pty and having one
            # available can confuse some commands, though we may need to make
            # this configurable in the future.
            'request_pty': False,
            # By default disable known_hosts checking (since most VMs expected to be dynamically created).
            'known_hosts': None,
        }

        if 'ssh_known_hosts_file' in self.config:
            self._connect_params['known_hosts'] = self.config.get("ssh_known_hosts_file", None)
            if isinstance(self._connect_params['known_hosts'], str):
                known_hosts_file = os.path.expanduser(self._connect_params['known_hosts'])
                if not os.path.exists(known_hosts_file):
                    raise ValueError(f"ssh_known_hosts_file {known_hosts_file} does not exist")
                self._connect_params['known_hosts'] = known_hosts_file
        if self._connect_params['known_hosts'] is None:
            _LOG.info("%s known_hosts checking is disabled per config.", self)

        if 'ssh_keepalive_interval' in self.config:
            keepalive_internal = self.config.get('ssh_keepalive_interval')
            self._connect_params['keepalive_interval'] = None if keepalive_internal is None else int(keepalive_internal)

    def _enter_context(self) -> "SshService":
        # Start the background thread if it's not already running.
        assert not self._in_context
        SshService._EVENT_LOOP_CONTEXT.enter()
        SshService._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE.enter()
        super()._enter_context()
        return self

    def _exit_context(self, ex_type: Optional[Type[BaseException]],
                      ex_val: Optional[BaseException],
                      ex_tb: Optional[TracebackType]) -> Literal[False]:
        # Stop the background thread if it's not needed anymore and potentially
        # cleanup the cache as well.
        assert self._in_context
        SshService._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE.exit()
        SshService._EVENT_LOOP_CONTEXT.exit()
        return super()._exit_context(ex_type, ex_val, ex_tb)

    @classmethod
    def clear_client_cache(cls) -> None:
        """
        Clears the cache of client connections.
        Note: This may cause in flight operations to fail.
        """
        cls._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE.cleanup()

    def _run_coroutine(self, coro: Coroutine[Any, Any, CoroReturnType]) -> FutureReturnType:
        """
        Runs the given coroutine in the background event loop thread.

        Parameters
        ----------
        coro : Coroutine[Any, Any, CoroReturnType]
            The coroutine to run.

        Returns
        -------
        Future[CoroReturnType]
            A future that will be completed when the coroutine completes.
        """
        assert self._in_context
        return self._EVENT_LOOP_CONTEXT.run_coroutine(coro)

    def _get_connect_params(self, params: dict) -> dict:
        """
        Produces a dict of connection parameters for asyncssh.create_connection.

        Parameters
        ----------
        params : dict
            Additional connection parameters specific to this host.

        Returns
        -------
        dict
            A dict of connection parameters for asyncssh.create_connection.
        """
        # Setup default connect_params dict for all SshClients we might need to create.

        # Note: None is an acceptable value for several of these, in which case
        # reasonable defaults or values from ~/.ssh/config will take effect.

        # Start with the base config params.
        connect_params = self._connect_params.copy()

        connect_params['host'] = params['ssh_hostname']     # required

        if params.get('ssh_port'):
            connect_params['port'] = int(params.pop('ssh_port'))
        elif self.config['ssh_port']:
            connect_params['port'] = int(self.config['ssh_port'])

        if 'ssh_username' in params:
            connect_params['username'] = str(params.pop('ssh_username'))
        elif self.config['ssh_username']:
            connect_params['username'] = str(self.config['ssh_username'])

        priv_key_file: Optional[str] = params.get('ssh_priv_key_path', self.config['ssh_priv_key_path'])
        if priv_key_file:
            priv_key_file = os.path.expanduser(priv_key_file)
            if not os.path.exists(priv_key_file):
                raise ValueError(f"ssh_priv_key_path {priv_key_file} does not exist")
            connect_params['client_keys'] = [priv_key_file]

        return connect_params

    async def _get_client_connection(self, params: dict) -> Tuple[SSHClientConnection, SshClient]:
        """
        Gets a (possibly cached) SshClient (connection) for the given connection params.

        Parameters
        ----------
        params : dict
            Optional override connection parameters.

        Returns
        -------
        Tuple[SSHClientConnection, SshClient]
            The connection and client objects.
        """
        assert self._in_context
        return await SshService._EVENT_LOOP_THREAD_SSH_CLIENT_CACHE.get_client_connection(self._get_connect_params(params))
