#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Protocol interface for helper functions to lookup and load configs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from mlos_bench.config.schemas.config_schemas import ConfigSchema
from mlos_bench.tunables.tunable_types import TunableValue

# Avoid's circular import issues.
if TYPE_CHECKING:
    from mlos_bench.environments.base_environment import Environment
    from mlos_bench.services.base_service import Service
    from mlos_bench.tunables.tunable_groups import TunableGroups


@runtime_checkable
class SupportsConfigLoading(Protocol):
    """Protocol interface for helper functions to lookup and load configs."""

    # Needed by pyright
    # pylint: disable=unnecessary-ellipsis,redundant-returns-doc

    def get_config_paths(self) -> list[str]:
        """
        Gets the list of config paths this service will search for config files.

        Returns
        -------
        list[str]
        """
        ...

    def resolve_path(self, file_path: str, extra_paths: Iterable[str] | None = None) -> str:
        """
        Prepend the suitable `_config_path` to `path` if the latter is not absolute. If
        `_config_path` is `None` or `path` is absolute, return `path` as is.

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
        ...

    def load_config(
        self,
        json: str,
        schema_type: ConfigSchema | None,
    ) -> dict | list[dict]:
        """
        Load JSON config file. Search for a file relative to `_config_path` if the input
        path is not absolute. This method is exported to be used as a service.

        Parameters
        ----------
        json : str
            Path to the input config file or a JSON string.
        schema_type : ConfigSchema | None
            The schema type to validate the config against.

        Returns
        -------
        config : Union[dict, list[dict]]
            Free-format dictionary that contains the configuration.
        """
        ...

    def build_environment(  # pylint: disable=too-many-arguments
        self,
        config: dict,
        tunables: TunableGroups,
        global_config: dict | None = None,
        parent_args: dict[str, TunableValue] | None = None,
        service: Service | None = None,
    ) -> Environment:
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Factory method for a new environment with a given config.

        Parameters
        ----------
        config : dict
            A dictionary with three mandatory fields:
                "name": Human-readable string describing the environment;
                "class": FQN of a Python class to instantiate;
                "config": Free-format dictionary to pass to the constructor.
        tunables : TunableGroups
            A (possibly empty) collection of groups of tunable parameters for
            all environments.
        global_config : dict | None
            Global parameters to add to the environment config.
        parent_args : dict[str, TunableValue] | None
            An optional reference of the parent CompositeEnv's const_args used to
            expand dynamic config parameters from.
        service: Service | None
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).

        Returns
        -------
        env : Environment
            An instance of the `Environment` class initialized with `config`.
        """
        ...

    def load_environment(
        self,
        json: str,
        tunables: TunableGroups,
        global_config: dict[str, Any] | None = None,
        parent_args: dict[str, TunableValue] | None = None,
        service: Service | None = None,
    ) -> Environment:
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Load and build new :py:class:`.Environment` from the config file or JSON string.

        Parameters
        ----------
        json : str
            The environment JSON configuration file or JSON string.
        tunables : TunableGroups
            A (possibly empty) collection of tunables to add to the environment.
        global_config : dict
            Global parameters to add to the environment config.
        parent_args : dict[str, TunableValue]
            An optional reference of the parent CompositeEnv's const_args used to
            expand dynamic config parameters from.
        service : Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        env : Environment
            A new benchmarking environment.
        """
        ...

    def load_environment_list(
        self,
        json: str,
        tunables: TunableGroups,
        global_config: dict | None = None,
        parent_args: dict[str, TunableValue] | None = None,
        service: Service | None = None,
    ) -> list[Environment]:
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Load and build a list of environments from the config file.

        Parameters
        ----------
        json : str
            The environment JSON configuration file or a JSON string.
            Can contain either one environment or a list of environments.
        tunables : TunableGroups
            A (possibly empty) collection of tunables to add to the environment.
        global_config : dict | None
            Global parameters to add to the environment config.
        parent_args : dict[str, TunableValue] | None
            An optional reference of the parent CompositeEnv's const_args used to
            expand dynamic config parameters from.
        service : Service | None
            An optional reference of the parent service to mix in.

        Returns
        -------
        env : list[Environment]
            A list of new benchmarking environments.
        """
        ...

    def load_services(
        self,
        jsons: Iterable[str],
        global_config: dict[str, Any] | None = None,
        parent: Service | None = None,
    ) -> Service:
        """
        Read the configuration files and bundle all service methods from those configs
        into a single Service object.

        Parameters
        ----------
        jsons : list of str
            A list of service JSON configuration files or JSON strings.
        global_config : dict
            Global parameters to add to the service config.
        parent : Service
            An optional reference of the parent service to mix in.

        Returns
        -------
        service : Service
            A collection of service methods.
        """
        ...
