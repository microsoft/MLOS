#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base class for an interface between the benchmarking framework
and mlos_core optimizers.
"""

import logging
from abc import ABCMeta, abstractmethod
from distutils.util import strtobool    # pylint: disable=deprecated-module

from types import TracebackType
from typing import Dict, Optional, Sequence, Tuple, Type, Union
from typing_extensions import Literal

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.services.base_service import Service
from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class Optimizer(metaclass=ABCMeta):     # pylint: disable=too-many-instance-attributes
    """
    An abstract interface between the benchmarking framework and mlos_core optimizers.
    """

    # See Also: mlos_bench/mlos_bench/config/schemas/optimizers/optimizer-schema.json
    BASE_SUPPORTED_CONFIG_PROPS = {
        "optimization_target",
        "optimization_direction",
        "max_iterations",
        "seed",
        "start_with_defaults",
    }

    def __init__(self,
                 tunables: TunableGroups,
                 config: dict,
                 global_config: Optional[dict] = None,
                 service: Optional[Service] = None):
        """
        Create a new optimizer for the given configuration space defined by the tunables.

        Parameters
        ----------
        tunables : TunableGroups
            The tunables to optimize.
        config : dict
            Free-format key/value pairs of configuration parameters to pass to the optimizer.
        global_config : Optional[dict]
        service : Optional[Service]
        """
        _LOG.info("Create optimizer for: %s", tunables)
        _LOG.debug("Optimizer config: %s", config)
        self._validate_json_config(config)
        self._config = config.copy()
        self._global_config = global_config or {}
        self._tunables = tunables
        self._service = service
        self._seed = int(config.get("seed", 42))
        self._in_context = False

        experiment_id = self._global_config.get('experiment_id')
        self.experiment_id = str(experiment_id).strip() if experiment_id else None

        self._iter = 1
        # If False, use the optimizer to suggest the initial configuration;
        # if True (default), use the already initialized values for the first iteration.
        self._start_with_defaults: bool = bool(
            strtobool(str(self._config.pop('start_with_defaults', True))))
        self._max_iter = int(self._config.pop('max_iterations', 100))
        self._opt_target = str(self._config.pop('optimization_target', 'score'))
        self._opt_sign = {"min": 1, "max": -1}[self._config.pop('optimization_direction', 'min')]

    def _validate_json_config(self, config: dict) -> None:
        """
        Reconstructs a basic json config that this class might have been
        instantiated from in order to validate configs provided outside the
        file loading mechanism.
        """
        json_config: dict = {
            "class": self.__class__.__module__ + "." + self.__class__.__name__,
        }
        if config:
            json_config["config"] = config
        ConfigSchema.OPTIMIZER.validate(json_config)

    def __repr__(self) -> str:
        opt_direction = 'min' if self.is_min else 'max'
        return f"{self.name}:{opt_direction}({self.target})(config={self._config})"

    def __enter__(self) -> 'Optimizer':
        """
        Enter the optimizer's context.
        """
        _LOG.debug("Optimizer START :: %s", self)
        assert not self._in_context
        self._in_context = True
        return self

    def __exit__(self, ex_type: Optional[Type[BaseException]],
                 ex_val: Optional[BaseException],
                 ex_tb: Optional[TracebackType]) -> Literal[False]:
        """
        Exit the context of the optimizer.
        """
        if ex_val is None:
            _LOG.debug("Optimizer END :: %s", self)
        else:
            assert ex_type and ex_val
            _LOG.warning("Optimizer END :: %s", self, exc_info=(ex_type, ex_val, ex_tb))
        assert self._in_context
        self._in_context = False
        return False  # Do not suppress exceptions

    @property
    def seed(self) -> int:
        """
        The random seed for the optimizer.
        """
        return self._seed

    @property
    def start_with_defaults(self) -> bool:
        """
        Return True if the optimizer should start with the default values.
        Note: This parameter is mutable and will be reset to False after the
        defaults are first suggested.
        """
        return self._start_with_defaults

    @property
    def tunable_params(self) -> TunableGroups:
        """
        Get the configuration space of the optimizer.

        Returns
        -------
        tunables : TunableGroups
            A collection of covariant groups of tunable parameters.
        """
        return self._tunables

    @property
    def name(self) -> str:
        """
        The name of the optimizer. We save this information in
        mlos_bench storage to track the source of each configuration.
        """
        return self.__class__.__name__

    # TODO: Expand these properties for multi-objective.

    @property
    def is_min(self) -> bool:
        """
        True if minimizing, False otherwise. Minimization is the default.
        """
        return self._opt_sign > 0

    @property
    def target(self) -> str:
        """
        The name of the target metric to optimize.
        """
        return self._opt_target

    @property
    def direction(self) -> str:
        """
        The direction to optimize the target metric (e.g., min or max).
        """
        return 'min' if self.is_min else 'max'

    @property
    def supports_preload(self) -> bool:
        """
        Return True if the optimizer supports pre-loading the data from previous experiments.
        """
        return True

    @abstractmethod
    def bulk_register(self, configs: Sequence[dict], scores: Sequence[Optional[float]],
                      status: Optional[Sequence[Status]] = None) -> bool:
        """
        Pre-load the optimizer with the bulk data from previous experiments.

        Parameters
        ----------
        configs : Sequence[dict]
            Records of tunable values from other experiments.
        scores : Sequence[float]
            Benchmark results from experiments that correspond to `configs`.
        status : Optional[Sequence[float]]
            Status of the experiments that correspond to `configs`.

        Returns
        -------
        is_not_empty : bool
            True if there is data to register, false otherwise.
        """
        _LOG.info("Warm-up the optimizer with: %d configs, %d scores, %d status values",
                  len(configs or []), len(scores or []), len(status or []))
        if len(configs or []) != len(scores or []):
            raise ValueError("Numbers of configs and scores do not match.")
        if status is not None and len(configs or []) != len(status or []):
            raise ValueError("Numbers of configs and status values do not match.")
        has_data = bool(configs and scores)
        if has_data and self._start_with_defaults:
            _LOG.info("Prior data exists - do *NOT* use the default initialization.")
            self._start_with_defaults = False
        return has_data

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
                 score: Optional[Union[float, Dict[str, float]]] = None) -> Optional[float]:
        """
        Register the observation for the given configuration.

        Parameters
        ----------
        tunables : TunableGroups
            The configuration that has been benchmarked.
            Usually it's the same config that the `.suggest()` method returned.
        status : Status
            Final status of the experiment (e.g., SUCCEEDED or FAILED).
        score : Union[float, Dict[str, float]]
            A scalar or a dict with the final benchmark results.
            None if the experiment was not successful.

        Returns
        -------
        value : float
            The scalar benchmark score extracted (and possibly transformed) from the dataframe that's being minimized.
        """
        _LOG.info("Iteration %d :: Register: %s = %s score: %s",
                  self._iter, tunables, status, score)
        if status.is_succeeded() == (score is None):  # XOR
            raise ValueError("Status and score must be consistent.")
        return self._get_score(status, score)

    def _get_score(self, status: Status, score: Optional[Union[float, Dict[str, float]]]) -> Optional[float]:
        """
        Extract a scalar benchmark score from the dataframe.
        Change the sign if we are maximizing.

        Parameters
        ----------
        status : Status
            Final status of the experiment (e.g., SUCCEEDED or FAILED).
        score : Union[float, Dict[str, float]]
            A scalar or a dict with the final benchmark results.
            None if the experiment was not successful.

        Returns
        -------
        score : float
            A scalar benchmark score to be used as a primary target for MINIMIZATION.
        """
        if not status.is_completed():
            return None
        if status.is_succeeded():
            assert score is not None
            if isinstance(score, dict):
                score = score[self._opt_target]
            return float(score) * self._opt_sign
        assert score is None
        return float("inf")

    def not_converged(self) -> bool:
        """
        Return True if not converged, False otherwise.
        Base implementation just checks the iteration count.
        """
        return self._iter <= self._max_iter

    @abstractmethod
    def get_best_observation(self) -> Union[Tuple[float, TunableGroups], Tuple[None, None]]:
        """
        Get the best observation so far.

        Returns
        -------
        (value, tunables) : Tuple[float, TunableGroups]
            The best value and the corresponding configuration.
            (None, None) if no successful observation has been registered yet.
        """
