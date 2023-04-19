#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for helper functions to lookup and load configs.
"""

from typing import List, Iterable, Optional, Union, Protocol, runtime_checkable, TYPE_CHECKING


# Avoid's circular import issues.
if TYPE_CHECKING:
    from mlos_bench.tunables.tunable_groups import TunableGroups
    from mlos_bench.service.base_service import Service
    from mlos_bench.environment.base_environment import Environment


@runtime_checkable
class SupportsConfigLoading(Protocol):
    """
    Protocol interface for helper functions to lookup and load configs.
    """

    def resolve_path(self, file_path: str,
                     extra_paths: Optional[Iterable[str]] = None) -> str:
        """
        Prepend the suitable `_config_path` to `path` if the latter is not absolute.
        If `_config_path` is `None` or `path` is absolute, return `path` as is.

        Parameters
        ----------
        file_path : str
            Path to the input config file.
        extra_paths : Iterable[str]
            Additional directories to prepend to the list of search paths.

        Returns
        -------
        path : str
            An actual path to the config or script.
        """

    def load_config(self, json_file_name: str) -> Union[dict, List[dict]]:
        """
        Load JSON config file. Search for a file relative to `_config_path`
        if the input path is not absolute.
        This method is exported to be used as a service.

        Parameters
        ----------
        json_file_name : str
            Path to the input config file.

        Returns
        -------
        config : Union[dict, List[dict]]
            Free-format dictionary that contains the configuration.
        """

    def build_environment(self, config: dict,
                          global_config: Optional[dict] = None,
                          tunables: Optional["TunableGroups"] = None,
                          service: Optional["Service"] = None) -> "Environment":
        """
        Factory method for a new environment with a given config.

        Parameters
        ----------
        config : dict
            A dictionary with three mandatory fields:
                "name": Human-readable string describing the environment;
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        global_config : dict
            Global parameters to add to the environment config.
        tunables : TunableGroups
            A collection of groups of tunable parameters for all environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).

        Returns
        -------
        env : Environment
            An instance of the `Environment` class initialized with `config`.
        """

    def load_environment_list(
            self, json_file_name: str, global_config: Optional[dict] = None,
            tunables: Optional["TunableGroups"] = None, service: Optional["Service"] = None) -> List["Environment"]:
        """
        Load and build a list of environments from the config file.

        Parameters
        ----------
        json_file_name : str
            The environment JSON configuration file.
            Can contain either one environment or a list of environments.
        global_config : dict
            Global parameters to add to the environment config.
        tunables : TunableGroups
            An optional collection of tunables to add to the environment.
        service : Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        env : List[Environment]
            A list of new benchmarking environments.
        """
