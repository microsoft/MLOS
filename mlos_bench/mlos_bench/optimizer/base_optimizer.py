#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base class for an interface between the benchmarking framework
and mlos_core optimizers.
"""

import logging
from typing import Tuple, List, Union
from abc import ABCMeta, abstractmethod

from mlos_bench.environment.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import prepare_class_load, instantiate_from_config

_LOG = logging.getLogger(__name__)


class Optimizer(metaclass=ABCMeta):
    """
    An abstract interface between the benchmarking framework and mlos_core optimizers.
    """

    @staticmethod
    def load(tunables: TunableGroups, config: dict, global_config: dict = None):
        """
        Instantiate the Optimizer shim from the configuration.

        Parameters
        ----------
        tunables : TunableGroups
            Tunable parameters of the environment.
        config : dict
            Configuration of the optimizer.
        global_config : dict
            Global configuration parameters (optional).

        Returns
        -------
        opt : Optimizer
            A new Optimizer instance.
        """
        (class_name, opt_config) = prepare_class_load(config, global_config)
        opt = Optimizer.new(class_name, tunables, opt_config)
        _LOG.info("Created optimizer: %s", opt)
        return opt

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
            An instance of the `Optimizer` class initialized with `config`.
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
        self._opt_target = self._config.pop('maximize', None)
        if self._opt_target is None:
            self._opt_target = self._config.pop('minimize', 'score')
            self._opt_sign = 1
        else:
            if 'minimize' in self._config:
                raise ValueError("Cannot specify both 'maximize' and 'minimize'.")
            self._opt_sign = -1

    @abstractmethod
    def bulk_register(self, data: List[dict]):
        """
        Pre-load the optimizer with the bulk data from previous experiments.

        Parameters
        ----------
        data : List[dict]
            Records of tunable values and benchmark scores from other experiments.
            The data is expected to be in `pandas.DataFrame.to_dict('records')` format.
        """

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
    def register(self, tunables: TunableGroups, status: Status,
                 score: Union[float, dict] = None) -> float:
        """
        Register the observation for the given configuration.

        Parameters
        ----------
        tunables : TunableGroups
            The configuration that has been benchmarked.
            Usually it's the same config that the `.suggest()` method returned.
        status : Status
            Final status of the experiment (e.g., SUCCEEDED or FAILED).
        score : Union[float, dict]
            A scalar or a dict with the final benchmark results.
            None if the experiment was not successful.

        Returns
        -------
        value : float
            A scalar benchmark score to MINIMIZE.
        """
        _LOG.info("Iteration %d :: Register: %s = %s score: %s",
                  self._iter, tunables, status, score)
        if status.is_succeeded == (score is None):  # XOR
            raise ValueError("Status and score must be consistent.")
        return self._get_score(status, score)

    def _get_score(self, status: Status, score: Union[float, dict]) -> float:
        """
        Extract a scalar benchmark score from the dataframe.
        Change the sign if we are maximizing.

        Parameters
        ----------
        status : Status
            Final status of the experiment (e.g., SUCCEEDED or FAILED).
        score : Union[float, dict]
            A scalar or a dict with the final benchmark results.
            None if the experiment was not successful.

        Returns
        -------
        score : float
            A scalar benchmark score to be used as a primary target for MINIMIZATION.
        """
        if not status.is_succeeded:
            return None
        if isinstance(score, dict):
            score = score[self._opt_target]
        return score * self._opt_sign

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
