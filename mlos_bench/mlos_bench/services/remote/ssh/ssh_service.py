from abc import ABCMeta
from typing import Optional

import os

from mlos_bench.services.base_service import Service
from mlos_bench.util import check_required_params


class SshService(Service, metaclass=ABCMeta):

    _REQUEST_TIMEOUT: Optional[float] = None  # seconds

    def __init__(self, config: dict, global_config: dict, parent: Service):
        super().__init__(config, global_config, parent)

        check_required_params(
            config, {
                "username",
                "hostname",
            }
        )

        self._request_timeout = config.get("requestTimeout", self._REQUEST_TIMEOUT)
        self._request_timeout = float(self._request_timeout) if self._request_timeout is not None else None
        self._username = config["username"]
        self._ssh_auth_socket = os.environ.get("SSH_AUTH_SOCK")
        self._priv_key_file = config.get("priv_key_file", None)
        if not self._priv_key_file:
            for key_file in ("id_rsa", "id_dsa", "id_ecdsa"):
                key_file_path = os.path.join(os.path.expanduser("~"), ".ssh", key_file)
                if os.path.exists(key_file_path):
                    self._priv_key_file = os.path.abspath(key_file_path)
                    break
        if not self._priv_key_file and not self._ssh_auth_socket:
            raise ValueError("Missing priv_key_file parameter and no default key file found in ~/.ssh")
        self._hostname = config["hostname"]
        self._port = config.get("port", 22)
        self._known_hosts_file = config.get("known_hosts_file", None)
        # TODO: Check that the file exists?

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(username={self._username}, priv_key_file={self._priv_key_file}, " \
               + "hostname={self._hostname}, port={self._port})"
