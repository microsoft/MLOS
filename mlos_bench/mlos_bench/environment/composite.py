"""
Composite benchmark environment.
"""

import logging

from mlos_bench.environment.base_environment import Environment
from mlos_bench.environment.persistence import build_environment

_LOG = logging.getLogger(__name__)


class CompositeEnv(Environment):
    """
    Composite benchmark environment.
    """

    def __init__(self, name, config, tunables, service=None):
        """
        Create a new environment with a given config.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the environment
            configuration. Must have a "children" section.
        tunables : TunableGroups
            A collection of groups of tunable parameters for *all* environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).
        """
        super().__init__(name, config, tunables, service)

        # Propagate all config parameters except "children" to every child config.
        shared_config = config.copy()
        del shared_config["children"]

        self._children = []
        for child_config in config["children"]:

            local_config = shared_config.copy()
            local_config.update(child_config.get("config", {}))
            child_config["config"] = local_config

            env = build_environment(child_config, shared_config, tunables, self._service)
            self._children.append(env)
            self._tunable_params.update(env.tunable_params())

    def setup(self):
        """
        Set up the children environments.

        Returns
        -------
        is_success : bool
            True if all children setup() operations are successful,
            false otherwise.
        """
        _LOG.debug("Set up: %s", self._children)
        return all(env.setup() for env in self._children)

    def teardown(self):
        """
        Tear down the children environments.

        Returns
        -------
        is_success : bool
            True if all children operations are successful, false otherwise.
        """
        reverse_children = self._children.copy().reverse()
        _LOG.debug("Tear down: %s", reverse_children)
        return all(env.teardown() for env in reverse_children)

    def run(self, tunables):
        """
        Submit a new experiment to the environment.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of groups of tunable parameters and their values
            from all children environments.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.debug("Run: %s with %s", self._children, tunables)
        return all(env.run(tunables) for env in self._children)

    def result(self):
        """
        Get the results of the benchmark.

        Returns
        -------
        (benchmark_status, benchmark_result) : (enum, float)
            A pair of (benchmark status, benchmark result) values.
            benchmark_status is of type mlos_bench.environment.Status.
            benchmark_result is a floating point time of the benchmark in
            seconds or None if the status is not COMPLETED.
        """
        # For now, we just return the result of the last child environment
        # in the sequence. TODO: have a way to select the right result from
        # the children, or identify which environment actually provides the
        # final result that will be used in the optimization.
        return self._children[-1].result()
