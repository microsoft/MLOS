#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection functions for interacting with SSH servers as file shares.
"""


from abc import ABCMeta
from typing import Optional

import logging
import os

import asyncssh

from mlos_bench.services.base_service import Service

_LOG = logging.getLogger(__name__)


class SshService(Service, metaclass=ABCMeta):
    """
    Base class for SSH services.
    """

    _REQUEST_TIMEOUT: Optional[float] = None  # seconds

    def __init__(self, config: dict, global_config: dict, parent: Optional[Service]):
        super().__init__(config, global_config, parent)

        self._request_timeout = config.get("requestTimeout", self._REQUEST_TIMEOUT)
        self._request_timeout = float(self._request_timeout) if self._request_timeout is not None else None

        # Note: None is an acceptable value for both ssh_username and ssh_port
        # to allow defaults in ~/.ssh/config to take effect.
        self._ssh_username = config.get("ssh_username")
        self._ssh_port = config.get("ssh_port")
        self._ssh_port = int(self._ssh_port) if self._ssh_port is not None else None

        self._ssh_auth_socket = os.environ.get("SSH_AUTH_SOCK")
        self._priv_key_file = config.get("priv_key_file", None)
        if not self._priv_key_file:
            for key_file in ("id_rsa", "id_ecdsa", "id_dsa"):
                key_file_path = os.path.join(os.path.expanduser("~"), ".ssh", key_file)
                if os.path.exists(key_file_path):
                    # TODO: Ideally we also check that the file not encrypted,
                    # else it's not usable without an ssh-agent setup.
                    self._priv_key_file = os.path.abspath(key_file_path)
                    break
        else:
            self._priv_key_file = os.path.abspath(os.path.expanduser(self._priv_key_file))
            if not os.path.exists(self._priv_key_file):
                raise ValueError(f"priv_key_file {self._priv_key_file} does not exist")
        if not self._priv_key_file and not self._ssh_auth_socket:
            raise ValueError("Missing priv_key_file parameter and no default key file found in ~/.ssh")

        self._known_hosts_file = config.get("known_hosts_file", None)
        if self._known_hosts_file:
            self._known_hosts_file = os.path.expanduser(self._known_hosts_file)
            if not os.path.exists(self._known_hosts_file):
                raise ValueError(f"known_hosts_file {self._known_hosts_file} does not exist")

    # TODO: Connection handling.
