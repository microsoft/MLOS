#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base scriptable benchmark environment.
"""

import abc
import re
from typing import Dict, Iterable, Optional

from mlos_bench.environments.base_environment import Environment
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable_groups import TunableGroups


class ScriptEnv(Environment, metaclass=abc.ABCMeta):
    """
    Base Environment that runs scripts for setup/run/teardown.
    """

    _RE_INVALID = re.compile(r"[^a-zA-Z0-9_]")

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
            configuration. Each config must have at least the `tunable_params`
            and the `const_args` sections. It must also have at least one of
            the following parameters: {`setup`, `run`, `teardown`}.
            Additional parameters:
                * `script_params` - an array of parameters to pass to the script
                  as shell environment variables, and
                * `script_params_rename` - a dictionary of {to: from} mappings
                  of the script parameters. If not specified, replace all
                  non-alphanumeric characters with underscores.
            If neither `script_params` nor `script_params_rename` are specified,
            pass *all* parameters to the script.
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
        self._script_params_rename: Dict[str, str] = self.config.get("script_params_rename", {})

    def _get_env_params(self) -> Dict[str, str]:
        """
        Get the *shell* environment parameters to be passed to the script.

        Returns
        -------
        env_params : Dict[str, str]
            Parameters to pass as *shell* environment variables into the script.
            This is usually a subset of `_params` with some possible conversions.
        """
        rename: Dict[str, str]  # {to: from} mapping of the script parameters.
        if self._script_params is None:
            if self._script_params_rename:
                # Only rename specified - use it.
                rename = self._script_params_rename.copy()
            else:
                # Neither `script_params` nor rename are specified - use all params.
                rename = {self._RE_INVALID.sub("_", key): key for key in self._params}
        else:
            # Use `script_params` and rename if specified.
            rename = {self._RE_INVALID.sub("_", key): key for key in self._script_params}
            rename.update(self._script_params_rename)

        return {key_sub: str(self._params[key]) for (key_sub, key) in rename.items()}
