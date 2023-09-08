#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection functions for interacting with SSH servers as file shares.
"""


from abc import ABCMeta
from asyncio import AbstractEventLoop, Lock as CoroutineLock
from typing import Dict, Optional
from threading import Lock, Thread, Lock as ThreadLock

import logging
import os

import asyncio
import asyncssh

from asyncssh.connection import SSHClientConnection

from mlos_bench.services.base_service import Service

_LOG = logging.getLogger(__name__)


class SshClient(asyncssh.SSHClient):
    """
    A class to manage SSH connections to hosts.

    This attempts to handle connection reuse and reconnection and encapsulating
    some of the async aspects of the library.

    Used by the SshService to try and maintain a single connection to hosts,
    handle reconnects if possible, and use that to run commands rather than
    reconnect for each command.

    Parameters
    ----------
    connect_params : dict
    """

    def __init__(self, *args: tuple, **kwargs: dict):
        self._connect_params: dict = kwargs.pop('connect_params')
        self._connection: Optional[SSHClientConnection] = None
        self._connection_lock = Lock()
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.connect_params_to_repr(self._connect_params)})"

    def __hash__(self) -> int:
        return hash(repr(self))

    def __del__(self) -> None:
        try:
            self.disconnect()
        except Exception as ex:     # pylint: disable=broad-exception-caught
            _LOG.warning("Encountered an issue disconnecting during object destructor: %s", ex)

    @staticmethod
    def connect_params_to_repr(connect_params: dict) -> str:
        """
        Gets a string representation of the connection parameters.

        Useful for looking up existing SshClients.

        Parameters
        ----------
        connect_params : dict

        Returns
        -------
        str
        """
        return f"{connect_params['username']}@{connect_params['host']}:{connect_params['port']}"

    @property
    def connection(self) -> SSHClientConnection:
        """
        Gets the SSH client connection to the host.

        Note: May block.
        """
        with self._connection_lock:
            return self._connection if self._connection else self.connect()

    async def _async_connect(self) -> SSHClientConnection:
        connect_params = self._connect_params.copy()
        # TODO: Setup logger on ssh client?
        return await asyncssh.connect(**connect_params)

    def connect(self) -> SSHClientConnection:
        """
        Establishes a connection to the remote host using asyncssh.

        Note: May block.

        Returns
        -------
        asyncssh.SSHClientConnection
            Returns a connection to the host.
        """
        with self._connection_lock:
            if not self._connection:
                self._connection = asyncio.run(self._async_connect())
        return self._connection

    def disconnect(self) -> None:
        """
        Closes the connection to the host.
        """
        with self._connection_lock:
            if self._connection:
                connection = self._connection
                self._connection = None
                connection.close()

    # Override hooks provided by asyncssh.SSHClient:

    def connection_made(self, conn: SSHClientConnection) -> None:
        _LOG.debug("Connection to %s made: %s", self._connect_params['host'], conn)
        conn._port
        return super().connection_made(conn)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        _LOG.debug("Connection to %s lost: %s", self._connect_params['host'], exc)
        with self._connection_lock:
            self._connection = None
            if exc is not None:
                # Attempt to reconnect.
                if not self.connect():
                    raise ConnectionError(f"Connection to {self._connect_params['host']} lost: {exc}")
            # Else, manually disconnected.


class SshService(Service, metaclass=ABCMeta):
    """
    Base class for SSH services.
    """

    # AsyncSSH requires an asyncio event loop to be running to work.
    # However, that that event loop blocks the main thread.
    # To avoid having to change our entire API to use async/await, all the way
    # up the stack, we run the event loop that runs any async code in a
    # background thread and submit async code to it using
    # asyncio.run_coroutine_threadsafe, interacting with Futures after that.
    # This is a bit of a hack, but it works for now.
    #
    # The event loop is created on demand and shared across all SshService
    # instances, hence we need to lock it when doing the setup/teardown.
    # We ran tests to ensure that multiple requests can still be executing
    # concurrently inside that event loop so there should be no performance loss.
    #
    # Note: the tests were run to confirm that this works with two threads.
    # Using a larger thread pool requires a bit more work since asyncssh
    # requires that run() requests are submitted to the same event loop handler
    # that the connection was made on.
    #
    _event_loop: Optional[AbstractEventLoop] = None
    _event_loop_thread: Optional[Thread] = None

    _REQUEST_TIMEOUT: Optional[float] = None  # seconds

    # Cache of SshClient connections.
    # Note: we place this in the base class so it can be used across
    # SshHostService and SshFileShareService subclasses.
    _clients: Dict[str, SshClient] = {}
    _clients_lock = ThreadLock()

    def __init__(self, config: dict, global_config: dict, parent: Optional[Service]):
        super().__init__(config, global_config, parent)

        # None can be used to disable the request timeout.
        self._request_timeout = config.get("ssh_request_timeout", self._REQUEST_TIMEOUT)
        self._request_timeout = float(self._request_timeout) if self._request_timeout is not None else None

        # Setup default connect_params dict for all SshClients we might need to create.

        # Note: None is an acceptable value for several of these, in which case
        # reasonable defaults or values from ~/.ssh/config will take effect.

        self._connect_params: dict = {
            # In general scripted commands shouldn't need a pty and having one
            # available can confuse some commands, though we may need to make
            # this configurable in the future.
            'request_pty': False,
        }
        if 'ssh_keepalive_interval' in config:
            keepalive_internal = config.get('ssh_keepalive_interval')
            self._connect_params['keepalive_interval'] = int(keepalive_internal) if keepalive_internal is not None else None
        if config.get('ssh_username'):
            self._connect_params['username'] = str(config['ssh_username'])
        if config.get('ssh_port'):
            self._connect_params['port'] = int(config['ssh_port'])
        if 'ssh_known_hosts_file' in config:
            self._connect_params['known_hosts'] = config.get("ssh_known_hosts_file", None)
            if isinstance(self._connect_params['known_hosts'], str):
                known_hosts_file = os.path.expanduser(self._connect_params['known_hosts'])
                if not os.path.exists(known_hosts_file):
                    raise ValueError(f"ssh_known_hosts_file {known_hosts_file} does not exist")
                self._connect_params['known_hosts'] = known_hosts_file
        if 'ssh_priv_key_file' in config:
            priv_key_file = config.get("ssh_priv_key_file")
            if priv_key_file:
                priv_key_file = os.path.expanduser(priv_key_file)
                if not os.path.exists(priv_key_file):
                    raise ValueError(f"ssh_priv_key_file {priv_key_file} does not exist")
                self._connect_params['client_keys'] = [priv_key_file]

    def get_host_client(self, params: dict) -> SshClient:
        """
        Gets an SshClient for a host if one doesn't already exist.

        Parameters
        ----------
        params : dict
            Additional connection parameters specific to this host.

        Returns
        -------
        SshClient
        """
        connect_params: dict = self._connect_params.copy()
        connect_params['host'] = connect_params.pop('ssh_hostname')
        # Allow overriding certain params on a per host basis using const_args.
        connect_params['port'] = params.pop('ssh_port', connect_params['port'])
        connect_params['username'] = params.pop('ssh_username', connect_params['username'])
        ssh_client_id = SshClient.connect_params_to_repr(connect_params)

        ssh_client = self._clients.get(ssh_client_id, None)
        if ssh_client is None:
            ssh_client = SshClient(connect_params=connect_params)
            self._clients[ssh_client_id] = ssh_client
        return ssh_client
