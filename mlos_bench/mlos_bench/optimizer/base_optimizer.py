"""
Bse class for an interface between the benchmarking framework
and mlos_core optimizers.
"""

import logging
from typing import Tuple
from abc import ABCMeta, abstractmethod

from mlos_bench.environment.status import Status
from mlos_bench.environment.tunable import TunableGroups
from mlos_bench.util import instantiate_from_config

_LOG = logging.getLogger(__name__)


class Optimizer(metaclass=ABCMeta):
    """
    An abstract interface between the benchmarking framework and mlos_core optimizers.
    """

    @classmethod
    def new(cls, class_name: str, tunables: TunableGroups, config: dict):
        """
        Factory method for a new optimizer with a given config.

        Parameters
        ----------
        class_name: str
            FQN of a Python class to instantiate, e.g.,
            "mlos_bench.optimizer.MlosCoreOptimizer".
            Must be derived from the `Optimizer` class.
        tunables : TunableGroups
            The tunables to optimize.
        config : dict
            Free-format dictionary that contains the optimizer configuration.
            It will be passed as a constructor parameter of the class
            specified by `class_name`.

        Returns
        -------
        opt : Optimizer
            An instance of the `Optimzier` class initialized with `config`.
        """
        return instantiate_from_config(cls, class_name, tunables, config)

    def __init__(self, tunables: TunableGroups, config: dict):
        """
        Create a new optimizer for the given configuration space defined by the tunables.

        Parameters
        ----------
        tunables : TunableGroups
            The tunables to optimize.
        config : dict
            Free-format key/value pairs of configuration parameters to pass to the optimizer.
        """
        _LOG.info("Create optimizer for: %s", tunables)
        _LOG.debug("Optimizer config: %s", config)
        self._config = config.copy()
        self._tunables = tunables
        self._iter = 1
        self._max_iter = int(self._config.pop('max_iterations', 10))

    @abstractmethod
    def suggest(self) -> TunableGroups:
        """
        Generate the next suggestion.

        Returns
        -------
        tunables : TunableGroups
            The next configuration to benchmark.
            These are the same tunables we pass to the constructor,
            but with the values set to the next suggestion.
        """

    @abstractmethod
    def register(self, tunables: TunableGroups, status: Status, score: float):
        """
        Register the observation for the given configuration.

        Parameters
        ----------
        tunables : TunableGroups
            The configuration that has been benchmarked.
            Usually it's the same config that the `.suggest()` method returned.
        status : Status
            Final status of the experiment (e.g., SUCCEEDED or FAILED).
        score : float
            The benchmark result, or None if the experiment was not successful.
        """

    def not_converged(self) -> bool:
        """
        Return True if not converged, False otherwise.
        Base implementation just checks the iteration count.
        """
        return self._iter <= self._max_iter

    @abstractmethod
    def get_best_observation(self) -> Tuple[float, TunableGroups]:
        """
        Get the best observation so far.

        Returns
        -------
        (value, tunables) : Tuple[float, TunableGroups]
            The best value and the corresponding configuration.
            (None, None) if no successful observation has been registered yet.
        """
