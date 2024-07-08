#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A hierarchy of benchmark environments."""

import abc
import json
import logging
from datetime import datetime
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from pytz import UTC
from typing_extensions import Literal

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.dict_templater import DictTemplater
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
    """An abstract base of all benchmark environments."""

    @classmethod
    def new(
        cls,
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
            "mlos_bench.environments.remote.HostEnv".
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
            deploy or reboot a VM/Host, etc.).

        Returns
        -------
        env : Environment
            An instance of the `Environment` class initialized with `config`.
        """
        assert issubclass(cls, Environment)
        return instantiate_from_config(
            cls,
            class_name,
            name=env_name,
            config=config,
            global_config=global_config,
            tunables=tunables,
            service=service,
        )

    def __init__(
        self,
        *,
        name: str,
        config: dict,
        global_config: Optional[dict] = None,
        tunables: Optional[TunableGroups] = None,
        service: Optional[Service] = None,
    ):
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
            deploy or reboot a VM/Host, etc.).
        """
        self._validate_json_config(config, name)
        self.name = name
        self.config = config
        self._service = service
        self._service_context: Optional[Service] = None
        self._is_ready = False
        self._in_context = False
        self._const_args: Dict[str, TunableValue] = config.get("const_args", {})

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug(
                "Environment: '%s' Service: %s",
                name,
                self._service.pprint() if self._service else None,
            )

        if tunables is None:
            _LOG.warning(
                (
                    "No tunables provided for %s. "
                    "Tunable inheritance across composite environments may be broken."
                ),
                name,
            )
            tunables = TunableGroups()

        groups = self._expand_groups(
            config.get("tunable_params", []),
            (global_config or {}).get("tunable_params_map", {}),
        )
        _LOG.debug("Tunable groups for: '%s' :: %s", name, groups)

        self._tunable_params = tunables.subgroup(groups)

        # If a parameter comes from the tunables, do not require it in the const_args or globals
        req_args = set(config.get("required_args", [])) - set(
            self._tunable_params.get_param_values().keys()
        )
        merge_parameters(dest=self._const_args, source=global_config, required_keys=req_args)
        self._const_args = self._expand_vars(self._const_args, global_config or {})

        self._params = self._combine_tunables(self._tunable_params)
        _LOG.debug("Parameters for '%s' :: %s", name, self._params)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Config for: '%s'\n%s", name, json.dumps(self.config, indent=2))

    def _validate_json_config(self, config: dict, name: str) -> None:
        """Reconstructs a basic json config that this class might have been instantiated
        from in order to validate configs provided outside the file loading
        mechanism.
        """
        json_config: dict = {
            "class": self.__class__.__module__ + "." + self.__class__.__name__,
        }
        if name:
            json_config["name"] = name
        if config:
            json_config["config"] = config
        ConfigSchema.ENVIRONMENT.validate(json_config)

    @staticmethod
    def _expand_groups(
        groups: Iterable[str],
        groups_exp: Dict[str, Union[str, Sequence[str]]],
    ) -> List[str]:
        """
        Expand `$tunable_group` into actual names of the tunable groups.

        Parameters
        ----------
        groups : List[str]
            Names of the groups of tunables, maybe with `$` prefix (subject to expansion).
        groups_exp : dict
            A dictionary that maps dollar variables for tunable groups to the lists
            of actual tunable groups IDs.

        Returns
        -------
        groups : List[str]
            A flat list of tunable groups IDs for the environment.
        """
        res: List[str] = []
        for grp in groups:
            if grp[:1] == "$":
                tunable_group_name = grp[1:]
                if tunable_group_name not in groups_exp:
                    raise KeyError(
                        (
                            f"Expected tunable group name ${tunable_group_name} "
                            "undefined in {groups_exp}"
                        )
                    )
                add_groups = groups_exp[tunable_group_name]
                res += [add_groups] if isinstance(add_groups, str) else add_groups
            else:
                res.append(grp)
        return res

    @staticmethod
    def _expand_vars(
        params: Dict[str, TunableValue],
        global_config: Dict[str, TunableValue],
    ) -> dict:
        """Expand `$var` into actual values of the variables."""
        return DictTemplater(params).expand_vars(extra_source_dict=global_config)

    @property
    def _config_loader_service(self) -> "SupportsConfigLoading":
        assert self._service is not None
        return self._service.config_loader_service

    def __enter__(self) -> "Environment":
        """Enter the environment's benchmarking context."""
        _LOG.debug("Environment START :: %s", self)
        assert not self._in_context
        if self._service:
            self._service_context = self._service.__enter__()
        self._in_context = True
        return self

    def __exit__(
        self,
        ex_type: Optional[Type[BaseException]],
        ex_val: Optional[BaseException],
        ex_tb: Optional[TracebackType],
    ) -> Literal[False]:
        """Exit the context of the benchmarking environment."""
        ex_throw = None
        if ex_val is None:
            _LOG.debug("Environment END :: %s", self)
        else:
            assert ex_type and ex_val
            _LOG.warning("Environment END :: %s", self, exc_info=(ex_type, ex_val, ex_tb))
        assert self._in_context
        if self._service_context:
            try:
                self._service_context.__exit__(ex_type, ex_val, ex_tb)
            # pylint: disable=broad-exception-caught
            except Exception as ex:
                _LOG.error("Exception while exiting Service context '%s': %s", self._service, ex)
                ex_throw = ex
            finally:
                self._service_context = None
        self._in_context = False
        if ex_throw:
            raise ex_throw
        return False  # Do not suppress exceptions

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} :: '{self.name}'"

    def pprint(self, indent: int = 4, level: int = 0) -> str:
        """
        Pretty-print the environment configuration. For composite environments, print
        all children environments as well.

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
        ignore it (it might belong to another environment). This method should never
        mutate the original config or the tunables.

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
            into_params=self._const_args.copy(),
        )

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

    @property
    def parameters(self) -> Dict[str, TunableValue]:
        """
        Key/value pairs of all environment parameters (i.e., `const_args` and
        `tunable_params`). Note that before `.setup()` is called, all tunables will be
        set to None.

        Returns
        -------
        parameters : Dict[str, TunableValue]
            Key/value pairs of all environment parameters
            (i.e., `const_args` and `tunable_params`).
        """
        return self._params

    def setup(self, tunables: TunableGroups, global_config: Optional[dict] = None) -> bool:
        """
        Set up a new benchmark environment, if necessary. This method must be
        idempotent, i.e., calling it several times in a row should be equivalent to a
        single call.

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

        # Make sure we create a context before invoking setup/run/status/teardown
        assert self._in_context

        # Assign new values to the environment's tunable parameters:
        groups = list(self._tunable_params.get_covariant_group_names())
        self._tunable_params.assign(tunables.get_param_values(groups))

        # Write to the log whether the environment needs to be reset.
        # (Derived classes still have to check `self._tunable_params.is_updated()`).
        is_updated = self._tunable_params.is_updated()
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug(
                "Env '%s': Tunable groups reset = %s :: %s",
                self,
                is_updated,
                {
                    name: self._tunable_params.is_updated([name])
                    for name in self._tunable_params.get_covariant_group_names()
                },
            )
        else:
            _LOG.info("Env '%s': Tunable groups reset = %s", self, is_updated)

        # Combine tunables, const_args, and global config into `self._params`:
        self._params = self._combine_tunables(tunables)
        merge_parameters(dest=self._params, source=global_config)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Combined parameters:\n%s", json.dumps(self._params, indent=2))

        return True

    def teardown(self) -> None:
        """
        Tear down the benchmark environment.

        This method must be idempotent, i.e., calling it several times in a row should
        be equivalent to a single call.
        """
        _LOG.info("Teardown %s", self)
        # Make sure we create a context before invoking setup/run/status/teardown
        assert self._in_context
        self._is_ready = False

    def run(self) -> Tuple[Status, datetime, Optional[Dict[str, TunableValue]]]:
        """
        Execute the run script for this environment.

        For instance, this may start a new experiment, download results, reconfigure
        the environment, etc. Details are configurable via the environment config.

        Returns
        -------
        (status, timestamp, output) : (Status, datetime, dict)
            3-tuple of (Status, timestamp, output) values, where `output` is a dict
            with the results or None if the status is not COMPLETED.
            If run script is a benchmark, then the score is usually expected to
            be in the `score` field.
        """
        # Make sure we create a context before invoking setup/run/status/teardown
        assert self._in_context
        (status, timestamp, _) = self.status()
        return (status, timestamp, None)

    def status(self) -> Tuple[Status, datetime, List[Tuple[datetime, str, Any]]]:
        """
        Check the status of the benchmark environment.

        Returns
        -------
        (benchmark_status, timestamp, telemetry) : (Status, datetime, list)
            3-tuple of (benchmark status, timestamp, telemetry) values.
            `timestamp` is UTC time stamp of the status; it's current time by default.
            `telemetry` is a list (maybe empty) of (timestamp, metric, value) triplets.
        """
        # Make sure we create a context before invoking setup/run/status/teardown
        assert self._in_context
        timestamp = datetime.now(UTC)
        if self._is_ready:
            return (Status.READY, timestamp, [])
        _LOG.warning("Environment not ready: %s", self)
        return (Status.PENDING, timestamp, [])
