#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base scriptable benchmark environment.
"""

import abc
import logging
import re
from typing import Dict, Iterable, Optional

from mlos_bench.environments.base_environment import Environment
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

from mlos_bench.util import try_parse_val

_LOG = logging.getLogger(__name__)


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
                * `shell_env_params` - an array of parameters to pass to the script
                  as shell environment variables, and
                * `shell_env_params_rename` - a dictionary of {to: from} mappings
                  of the script parameters. If not specified, replace all
                  non-alphanumeric characters with underscores.
            If neither `shell_env_params` nor `shell_env_params_rename` are specified,
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

        self._shell_env_params: Optional[Iterable[str]] = self.config.get("shell_env_params")
        self._shell_env_params_rename: Dict[str, str] = self.config.get("shell_env_params_rename", {})

        results_stdout_pattern = self.config.get("results_stdout_pattern")
        self._results_stdout_pattern: Optional[re.Pattern[str]] = \
            re.compile(results_stdout_pattern) if results_stdout_pattern else None

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
        if self._shell_env_params is None:
            if self._shell_env_params_rename:
                # Only rename specified - use it.
                rename = self._shell_env_params_rename.copy()
            else:
                # FIXME: We should not be exposing all params by default.
                # Neither `shell_env_params` nor rename are specified - use all params.
                rename = {self._RE_INVALID.sub("_", key): key for key in self._params}
        else:
            # Use `shell_env_params` and rename if specified.
            rename = {self._RE_INVALID.sub("_", key): key for key in self._shell_env_params}
            rename.update(self._shell_env_params_rename)

        return {key_sub: str(self._params[key]) for (key_sub, key) in rename.items()}

    def _extract_stdout_results(self, stdout: str) -> Dict[str, TunableValue]:
        """
        Extract the results from the stdout of the script.

        Parameters
        ----------
        stdout : str
            The stdout of the script.

        Returns
        -------
        results : Dict[str, TunableValue]
            A dictionary of results extracted from the stdout.
        """
        if not self._results_stdout_pattern:
            return {}
        _LOG.debug("Extract regex: '%s' from: '%s'", self._results_stdout_pattern, stdout)
        return {key: try_parse_val(val) for (key, val) in self._results_stdout_pattern.findall(stdout)}
