#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection functions for interacting with SSH servers as file shares.
"""


from abc import ABCMeta
from typing import Dict, List, Optional, Union

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

    Used by the SshService.

    Parameters
    ----------
    connect_params : dict
    """

    def __init__(self, *args: tuple, **kwargs: dict):
        self._connect_params: dict = kwargs.pop('connect_params')
        self._connection: Optional[SSHClientConnection] = None
        super().__init__(*args, **kwargs)

    def __del__(self) -> None:
        if self._connection:
            self._connection.close()

    @property
    def connection(self) -> SSHClientConnection:
        """
        Gets the SSH client connection to the host.

        Note: May block.
        """
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
        if not self._connection:
            self._connection = asyncio.run(self._async_connect())
        return self._connection

    def close(self) -> None:
        """
        Closes the connection to the host.
        """
        if self._connection:
            self._connection.close()
            self._connection = None

    def connection_made(self, conn: SSHClientConnection) -> None:
        _LOG.debug("Connection to %s made: %s", self._connect_params['host'], conn)
        return super().connection_made(conn)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        _LOG.debug("Connection to %s lost: %s", self._connect_params['host'], exc)
        if not self.connect():
            raise ConnectionError(f"Connection to {self._connect_params['host']} lost: {exc}")


class SshService(Service, metaclass=ABCMeta):
    """
    Base class for SSH services.
    """

    _REQUEST_TIMEOUT: Optional[float] = None  # seconds

    def __init__(self, config: dict, global_config: dict, parent: Optional[Service]):
        super().__init__(config, global_config, parent)

        self._request_timeout = config.get("ssh_request_timeout", self._REQUEST_TIMEOUT)
        self._request_timeout = float(self._request_timeout) if self._request_timeout is not None else None

        # Note: None is an acceptable value for several of these, in which case
        # reasonable defaults or values from ~/.ssh/config will take effect.

        self._clients: Dict[str, SshClient] = {}
        self._connect_params: Dict[str, Union[None, int, str, List[str]]] = {
            'request_pty': False,
        }
        if 'ssh_keepalive_interval' in config:
            self._connect_params['keepalive_interval'] = config.get('ssh_keepalive_interval')
        if config.get('ssh_username'):
            self._connect_params['username'] = config['ssh_username']
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

    def connect_host(self, params: dict) -> SshClient:
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
        ssh_client = self._clients.get(params['ssh_hostname'])
        if ssh_client is None:
            connect_params: dict = self._connect_params.copy()
            connect_params['host'] = connect_params.pop('ssh_hostname')
            # Allow overriding certain params on a per host basis using const_args.
            connect_params['port'] = params.pop('ssh_port', connect_params['port'])
            connect_params['username'] = params.pop('ssh_username', connect_params['username'])
            ssh_client = SshClient(connect_params=connect_params)
            self._clients[params['ssh_hostname']] = ssh_client
        return ssh_client
