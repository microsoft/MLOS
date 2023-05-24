#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A hierarchy of benchmark environments.
"""

import abc
import json
import logging
from typing import Dict, Optional, Tuple, TYPE_CHECKING

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import instantiate_from_config, merge_parameters

if TYPE_CHECKING:
    from mlos_bench.services.types.config_loader_type import SupportsConfigLoading

_LOG = logging.getLogger(__name__)


class Environment(metaclass=abc.ABCMeta):
    # pylint: disable=too-many-instance-attributes
    """
    An abstract base of all benchmark environments.
    """

    @classmethod
    def new(cls,
            *,
            env_name: str,
            class_name: str,
            config: dict,
            global_config: Optional[dict] = None,
            tunables: Optional[TunableGroups] = None,
            service: Optional[Service] = None,
            ) -> "Environment":
        """
        Factory method for a new environment with a given config.

        Parameters
        ----------
        env_name: str
            Human-readable name of the environment.
        class_name: str
            FQN of a Python class to instantiate, e.g.,
            "mlos_bench.environments.remote.VMEnv".
            Must be derived from the `Environment` class.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. It will be passed as a constructor parameter of
            the class specified by `name`.
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
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
        return instantiate_from_config(
            cls,
            class_name,
            name=env_name,
            config=config,
            global_config=global_config,
            tunables=tunables,
            service=service
        )

    def __init__(self,
                 *,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
        """
        Create a new environment with a given config.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. Each config must have at least the "tunable_params"
            and the "const_args" sections.
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
        tunables : TunableGroups
            A collection of groups of tunable parameters for all environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).
        """
        self.name = name
        self.config = config
        self._service = service
        self._is_ready = False
        self._params: Dict[str, TunableValue] = {}
        self._const_args = config.get("const_args", {})

        merge_parameters(dest=self._const_args, source=global_config,
                         required_keys=config.get("required_args"))

        if tunables is None:
            _LOG.warning("No tunables provided for %s. Tunable inheritance across composite environments may be broken.", name)
            tunables = TunableGroups()

        tunable_groups = config.get("tunable_params")
        self._tunable_params = tunables.subgroup(tunable_groups) if tunable_groups else tunables

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Config for: %s\n%s",
                       name, json.dumps(self.config, indent=2))

    @property
    def _config_loader_service(self) -> "SupportsConfigLoading":
        assert self._service is not None
        return self._service.config_loader_service

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}::'{self.name}'"

    def pprint(self, indent: int = 4, level: int = 0) -> str:
        """
        Pretty-print the environment configuration.
        For composite environments, print all children environments as well.

        Parameters
        ----------
        indent : int
            Number of spaces to indent the output. Default is 4.
        level : int
            Current level of indentation. Default is 0.

        Returns
        -------
        pretty : str
            Pretty-printed environment configuration.
            Default output is the same as `__repr__`.
        """
        return f'{" " * indent * level}{repr(self)}'

    def _combine_tunables(self, tunables: TunableGroups) -> Dict[str, TunableValue]:
        """
        Plug tunable values into the base config. If the tunable group is unknown,
        ignore it (it might belong to another environment). This method should
        never mutate the original config or the tunables.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters
            along with the parameters' values.

        Returns
        -------
        params : Dict[str, Union[int, float, str]]
            Free-format dictionary that contains the new environment configuration.
        """
        return tunables.get_param_values(
            group_names=list(self._tunable_params.get_covariant_group_names()),
            into_params=self._const_args.copy())

    @property
    def tunable_params(self) -> TunableGroups:
        """
        Get the configuration space of the given environment.

        Returns
        -------
        tunables : TunableGroups
            A collection of covariant groups of tunable parameters.
        """
        return self._tunable_params

    def setup(self, tunables: TunableGroups, global_config: Optional[dict] = None) -> bool:
        """
        Set up a new benchmark environment, if necessary. This method must be
        idempotent, i.e., calling it several times in a row should be
        equivalent to a single call.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of tunable parameters along with their values.
        global_config : dict
            Free-format dictionary of global parameters of the environment
            that are not used in the optimization process.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("Setup %s :: %s", self, tunables)
        assert isinstance(tunables, TunableGroups)

        self._params = self._combine_tunables(tunables)
        merge_parameters(dest=self._params, source=global_config)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Combined parameters:\n%s", json.dumps(self._params, indent=2))

        return True

    def teardown(self) -> None:
        """
        Tear down the benchmark environment. This method must be idempotent,
        i.e., calling it several times in a row should be equivalent to a
        single call.
        """
        _LOG.info("Teardown %s", self)
        self._is_ready = False

    def run(self) -> Tuple[Status, Optional[dict]]:
        """
        Execute the run script for this environment.

        For instance, this may start a new experiment, download results, reconfigure
        the environment, etc. Details are configurable via the environment config.

        Returns
        -------
        (status, output) : (Status, dict)
            A pair of (Status, output) values, where `output` is a dict
            with the results or None if the status is not COMPLETED.
            If run script is a benchmark, then the score is usually expected to
            be in the `score` field.
        """
        return self.status()

    def status(self) -> Tuple[Status, Optional[dict]]:
        """
        Check the status of the benchmark environment.

        Returns
        -------
        (benchmark_status, telemetry) : (Status, dict)
            A pair of (benchmark status, telemetry) values.
            `telemetry` is a free-form dict or None if the environment is not running.
        """
        if self._is_ready:
            return (Status.READY, None)
        _LOG.warning("Environment not ready: %s", self)
        return (Status.PENDING, None)
