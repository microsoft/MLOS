#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base scriptable benchmark environment.
"""

import abc
import re
import logging
from typing import Dict, Iterable, Optional

from mlos_bench.environments.base_environment import Environment
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class ScriptEnv(Environment, metaclass=abc.ABCMeta):
    """
    Base Environment that runs scripts for setup/run/teardown.
    """

    def __init__(self,
                 *,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
        """
        Create a new environment for script execution.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. Each config must have at least the "tunable_params"
            and the "const_args" sections. It must also have at least one of
            the following parameters: {setup, run, teardown}
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
        tunables : TunableGroups
            A collection of tunable parameters for *all* environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).
        """
        super().__init__(name=name, config=config, global_config=global_config,
                         tunables=tunables, service=service)

        self._script_setup = self.config.get("setup")
        self._script_run = self.config.get("run")
        self._script_teardown = self.config.get("teardown")

        self._script_params: Optional[Iterable[str]] = self.config.get("script_params")

        if self._script_setup is None and \
           self._script_run is None and \
           self._script_teardown is None:
            raise ValueError("At least one of {setup, run, teardown} must be present")

    def _get_env_params(self) -> Dict[str, str]:
        """
        Get the *shell* environment parameters to be passed to the script.

        Returns
        -------
        env_params : Dict[str, str]
            Parameters to pass as *shell* environment variables into the script.
            This is usually a subset of `_params` with some possible conversions.
        """
        keys = self._params.keys() if self._script_params is None else self._script_params
        return {re.sub(r"\W", "_", key): str(self._params[key]) for key in keys}
