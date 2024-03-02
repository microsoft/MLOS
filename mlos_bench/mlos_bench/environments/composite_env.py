#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Composite benchmark environment.
"""

import itertools
import logging
from datetime import datetime

from types import TracebackType
from typing import Any, Dict, List, Optional, Tuple, Type
from typing_extensions import Literal

from mlos_bench.services.base_service import Service
from mlos_bench.environments.status import Status
from mlos_bench.environments.base_environment import Environment
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class CompositeEnv(Environment):
    """
    Composite benchmark environment.
    """

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
            Free-format dictionary that contains the environment
            configuration. Must have a "children" section.
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
        tunables : TunableGroups
            A collection of groups of tunable parameters for *all* environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).
        """
        super().__init__(name=name, config=config, global_config=global_config,
                         tunables=tunables, service=service)

        # By default, the Environment includes only the tunables explicitly specified
        # in the "tunable_params" section of the config. `CompositeEnv`, however, must
        # retain all tunables from its children environments plus the ones that come
        # from the "include_tunables".
        tunables = tunables.copy() if tunables else TunableGroups()

        _LOG.debug("Build composite environment '%s' START: %s", self, tunables)
        self._children: List[Environment] = []
        self._child_contexts: List[Environment] = []

        # To support trees of composite environments (e.g. for multiple VM experiments),
        # each CompositeEnv gets a copy of the original global config and adjusts it with
        # the `const_args` specific to it.
        global_config = (global_config or {}).copy()
        for (key, val) in self._const_args.items():
            global_config.setdefault(key, val)

        for child_config_file in config.get("include_children", []):
            for env in self._config_loader_service.load_environment_list(
                    child_config_file, tunables, global_config, self._const_args, self._service):
                self._add_child(env, tunables)

        for child_config in config.get("children", []):
            env = self._config_loader_service.build_environment(
                child_config, tunables, global_config, self._const_args, self._service)
            self._add_child(env, tunables)

        _LOG.debug("Build composite environment '%s' END: %s", self, self._tunable_params)

        if not self._children:
            raise ValueError("At least one child environment must be present")

    def __enter__(self) -> Environment:
        self._child_contexts = [env.__enter__() for env in self._children]
        return super().__enter__()

    def __exit__(self, ex_type: Optional[Type[BaseException]],
                 ex_val: Optional[BaseException],
                 ex_tb: Optional[TracebackType]) -> Literal[False]:
        ex_throw = None
        for env in reversed(self._children):
            try:
                env.__exit__(ex_type, ex_val, ex_tb)
            # pylint: disable=broad-exception-caught
            except Exception as ex:
                _LOG.error("Exception while exiting child environment '%s': %s", env, ex)
                ex_throw = ex
        self._child_contexts = []
        super().__exit__(ex_type, ex_val, ex_tb)
        if ex_throw:
            raise ex_throw
        return False

    @property
    def children(self) -> List[Environment]:
        """
        Return the list of child environments.
        """
        return self._children

    def pprint(self, indent: int = 4, level: int = 0) -> str:
        """
        Pretty-print the environment and its children.

        Parameters
        ----------
        indent : int
            Number of spaces to indent the output at each level. Default is 4.
        level : int
            Current level of indentation. Default is 0.

        Returns
        -------
        pretty : str
            Pretty-printed environment configuration.
        """
        return super().pprint(indent, level) + '\n' + '\n'.join(
            child.pprint(indent, level + 1) for child in self._children)

    def _add_child(self, env: Environment, tunables: TunableGroups) -> None:
        """
        Add a new child environment to the composite environment.
        This method is called from the constructor only.
        """
        _LOG.debug("Merge tunables: '%s' <- '%s' :: %s", self, env, env.tunable_params)
        self._children.append(env)
        self._tunable_params.merge(env.tunable_params)
        tunables.merge(env.tunable_params)

    def setup(self, tunables: TunableGroups, global_config: Optional[dict] = None) -> bool:
        """
        Set up the children environments.

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
            True if all children setup() operations are successful,
            false otherwise.
        """
        assert self._in_context
        _LOG.info("Setup: %s :: %s", self, self._children)
        is_success = super().setup(tunables, global_config) and all(
            env_context.setup(tunables, global_config) for env_context in self._child_contexts)
        _LOG.info("Setup: %s completed successfully: %s", self, is_success)
        return is_success

    def teardown(self) -> None:
        """
        Tear down the children environments. This method is idempotent,
        i.e., calling it several times is equivalent to a single call.
        The environments are being torn down in the reverse order.
        """
        assert self._in_context
        _LOG.info("Tear down: %s :: %s", self, self._children)
        for env_context in reversed(self._child_contexts):
            env_context.teardown()
        super().teardown()

    def run(self) -> bool:
        """
        Submit a new experiment to the environment.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        assert self._in_context
        _LOG.info("Run: %s :: %s", self, self._children)
        is_success = super().run() and all(
            env_context.run() for env_context in self._child_contexts)
        _LOG.info("Run: %s submitted successfully: %s", self, is_success)
        return is_success

    def results(self) -> Tuple[Status, datetime, Optional[Dict[str, TunableValue]]]:
        """
        Get the results of the trial launched by `.run()` call.
        Return the result of the *last* child environment if successful,
        or the status of the last failed environment otherwise.

        Returns
        -------
        (status, timestamp, output) : (Status, datetime, dict)
            3-tuple of (Status, timestamp, output) values, where `output` is a dict
            with the results or None if the status is not COMPLETED.
            If run script is a benchmark, then the score is usually expected to
            be in the `score` field.
        """
        _LOG.info("Get results: %s", self._children)
        (status, timestamp, metrics) = super().results()
        if status.is_in_setup():
            _LOG.debug("Env not ready: %s :: %s", self, status)
            return (status, timestamp, metrics)

        joint_metrics = {}
        for env_context in self._child_contexts:
            _LOG.debug("Get results: %s", env_context)
            (status, timestamp, metrics) = env_context.results()
            self._update(status, timestamp)
            _LOG.debug("Get results: %s :: %s %s", env_context, status, metrics)
            if not status.is_good():
                _LOG.info("Get results failed: %s :: %s", self, status)
                return (status, timestamp, None)
            joint_metrics.update(metrics or {})

        self._results = joint_metrics
        _LOG.info("Run completed: %s :: %s %s", self, status, self._results)
        # Return the status and the timestamp of the last child environment.
        return (status, timestamp, self._results)

    def status(self) -> Tuple[Status, datetime]:
        """
        Check the status of the benchmark environment.

        Returns
        -------
        (benchmark_status, timestamp) : (Status, datetime)
            A pair of (benchmark status, timestamp) values.
            `timestamp` is UTC time stamp of the status; it's current time by default.
        """
        (status, timestamp) = super().status()
        if status.is_in_setup():
            _LOG.debug("Env not ready: %s :: %s", self, status)
            return (status, timestamp)

        for env_context in self._child_contexts:
            _LOG.debug("Get status: %s", env_context)
            (status, timestamp) = env_context.status()
            self._update(status, timestamp)
            _LOG.debug("Get status: %s :: %s %s", env_context, status)
            if not status.is_good():
                _LOG.info("Get failed status: %s :: %s", self, status)
                break

        return (status, timestamp)

    def telemetry(self, timestamp: Optional[datetime] = None) -> List[Tuple[datetime, str, Any]]:
        """
        Get the telemetry data of the environment, if there is any.

        Parameters
        ----------
        timestamp : datetime
            UTC timestamp watermark of the telemetry data.
            If specified, return telemetry with timestamps greater than the given one.
            If None (default), return all telemetry data available.

        Returns
        -------
        telemetry : List[Tuple[datetime, str, Any]]
            A list (maybe empty) of (timestamp, metric, value) triplets.
        """
        return super().telemetry(timestamp) + list(itertools.chain(
            *[env_context.telemetry(timestamp) for env_context in self._child_contexts]
        ))
