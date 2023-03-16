"""
Composite benchmark environment.
"""

import logging
from typing import Optional, Tuple

import pandas

from mlos_bench.service.base_service import Service
from mlos_bench.environment.status import Status
from mlos_bench.environment.base_environment import Environment
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class CompositeEnv(Environment):
    """
    Composite benchmark environment.
    """

    def __init__(self, name: str, config: dict, global_config: dict = None,
                 tunables: TunableGroups = None, service: Service = None):
        # pylint: disable=too-many-arguments
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
        super().__init__(name, config, global_config, tunables, service)

        self._children = []

        for child_config_file in config.get("include_children", []):
            for env in self._service.load_environment_list(
                    child_config_file, global_config, tunables, self._service):
                self._add_child(env)

        for child_config in config.get("children", []):
            self._add_child(self._service.build_environment(
                child_config, global_config, tunables, self._service))

        if not self._children:
            raise ValueError("At least one child environment must be present")

    def _add_child(self, env: Environment):
        """
        Add a new child environment to the composite environment.
        This method is called from the constructor only.
        """
        self._children.append(env)
        self._tunable_params.update(env.tunable_params())

    def setup(self, tunables: TunableGroups) -> bool:
        """
        Set up the children environments.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of tunable parameters along with their values.

        Returns
        -------
        is_success : bool
            True if all children setup() operations are successful,
            false otherwise.
        """
        self._is_ready = (
            super().setup(tunables) and
            all(env.setup(tunables) for env in self._children)
        )
        return self._is_ready

    def teardown(self):
        """
        Tear down the children environments. This method is idempotent,
        i.e., calling it several times is equivalent to a single call.
        The environments are being torn down in the reverse order.
        """
        for env in reversed(self._children):
            env.teardown()
        super().teardown()

    def run(self) -> Tuple[Status, Optional[pandas.DataFrame]]:
        """
        Submit a new experiment to the environment.
        Return the result of the *last* child environment if successful,
        or the status of the last failed environment otherwise.

        Returns
        -------
        (status, output) : (Status, pandas.DataFrame)
            A pair of (Status, output) values, where `output` is a one-row DataFrame
            with the benchmark results or None if the status is not COMPLETED.
            Benchmark score is usually in the `score` column of the DataFrame.
        """
        _LOG.info("Run: %s", self._children)
        (status, _) = result = super().run()
        if not status.is_ready:
            return result
        for env in self._children:
            _LOG.debug("Child env. run: %s", env)
            (status, _) = result = env.run()
            _LOG.debug("Child env. run results: %s :: %s", env, result)
            if not status.is_good:
                break
        _LOG.info("Run completed: %s :: %s", self, result)
        return result
