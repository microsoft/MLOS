#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base class for an interface between the benchmarking framework and :py:mod:`mlos_core`
optimizers and other config suggestion methods.

See Also
--------
mlos_bench.optimizers :
    For more information on the available optimizers and their usage.
"""

import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from contextlib import AbstractContextManager as ContextManager
from types import TracebackType
from typing import Literal

from ConfigSpace import ConfigurationSpace

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.environments.status import Status
from mlos_bench.optimizers.convert_configspace import tunable_groups_to_configspace
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tunables.tunable_types import TunableValue
from mlos_bench.util import strtobool

_LOG = logging.getLogger(__name__)


class Optimizer(ContextManager, metaclass=ABCMeta):  # pylint: disable=too-many-instance-attributes
    """An abstract interface between the benchmarking framework and :py:mod:`mlos_core`
    optimizers and other config suggestion methods.
    """

    # See Also: mlos_bench/mlos_bench/config/schemas/optimizers/optimizer-schema.json
    BASE_SUPPORTED_CONFIG_PROPS = {
        "optimization_targets",
        "max_suggestions",
        "seed",
        "start_with_defaults",
    }

    def __init__(
        self,
        tunables: TunableGroups,
        config: dict,
        global_config: dict | None = None,
        service: Service | None = None,
    ):
        """
        Create a new optimizer for the given configuration space defined by the
        tunables.

        Parameters
        ----------
        tunables : TunableGroups
            The tunables to optimize.
        config : dict
            Free-format key/value pairs of configuration parameters to pass to the optimizer.
        global_config : dict | None
        service : Service | None
        """
        _LOG.info("Create optimizer for: %s", tunables)
        _LOG.debug("Optimizer config: %s", config)
        self._validate_json_config(config)
        self._config = config.copy()
        self._global_config = global_config or {}
        self._tunables = tunables
        self._config_space: ConfigurationSpace | None = None
        self._service = service
        self._seed = int(config.get("seed", 42))
        self._in_context = False

        experiment_id = self._global_config.get("experiment_id")
        self.experiment_id = str(experiment_id).strip() if experiment_id else None

        self._iter = 0
        # If False, use the optimizer to suggest the initial configuration;
        # if True (default), use the already initialized values for the first iteration.
        self._start_with_defaults: bool = bool(
            strtobool(str(self._config.pop("start_with_defaults", True)))
        )
        self._max_suggestions = int(self._config.pop("max_suggestions", 100))

        opt_targets: dict[str, str] = self._config.pop("optimization_targets", {"score": "min"})
        self._opt_targets: dict[str, Literal[1, -1]] = {}
        for opt_target, opt_dir in opt_targets.items():
            if opt_dir == "min":
                self._opt_targets[opt_target] = 1
            elif opt_dir == "max":
                self._opt_targets[opt_target] = -1
            else:
                raise ValueError(f"Invalid optimization direction: {opt_dir} for {opt_target}")

    def _validate_json_config(self, config: dict) -> None:
        """Reconstructs a basic json config that this class might have been instantiated
        from in order to validate configs provided outside the file loading
        mechanism.
        """
        json_config: dict = {
            "class": self.__class__.__module__ + "." + self.__class__.__name__,
        }
        if config:
            json_config["config"] = config
        ConfigSchema.OPTIMIZER.validate(json_config)

    def __repr__(self) -> str:
        opt_targets = ",".join(
            f"""{opt_target}:{({1: "min", -1: "max"}[opt_dir])}"""
            for (opt_target, opt_dir) in self._opt_targets.items()
        )
        return f"{self.name}({opt_targets},config={self._config})"

    def __enter__(self) -> "Optimizer":
        """Enter the optimizer's context."""
        _LOG.debug("Optimizer START :: %s", self)
        assert not self._in_context
        self._in_context = True
        return self

    def __exit__(
        self,
        ex_type: type[BaseException] | None,
        ex_val: BaseException | None,
        ex_tb: TracebackType | None,
    ) -> Literal[False]:
        """Exit the context of the optimizer."""
        if ex_val is None:
            _LOG.debug("Optimizer END :: %s", self)
        else:
            assert ex_type and ex_val
            _LOG.warning("Optimizer END :: %s", self, exc_info=(ex_type, ex_val, ex_tb))
        assert self._in_context
        self._in_context = False
        return False  # Do not suppress exceptions

    @property
    def current_iteration(self) -> int:
        """
        The current number of iterations (suggestions) registered.

        Note: this may or may not be the same as the number of configurations.
        See Also: Scheduler.trial_config_repeat_count and Scheduler.max_trials.
        """
        return self._iter

    @property
    def max_suggestions(self) -> int:
        """
        The maximum number of iterations (suggestions) to run.

        Note: this may or may not be the same as the number of configurations.
        See Also: Scheduler.trial_config_repeat_count and Scheduler.max_trials.
        """
        return self._max_suggestions

    @property
    def seed(self) -> int:
        """The random seed for the optimizer."""
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
        Get the tunable parameters of the optimizer as TunableGroups.

        Returns
        -------
        tunables : TunableGroups
            A collection of covariant groups of tunable parameters.
        """
        return self._tunables

    @property
    def config_space(self) -> ConfigurationSpace:
        """
        Get the tunable parameters of the optimizer as a ConfigurationSpace.

        Returns
        -------
        ConfigSpace.ConfigurationSpace
            The ConfigSpace representation of the tunable parameters.
        """
        if self._config_space is None:
            self._config_space = tunable_groups_to_configspace(self._tunables, self._seed)
            _LOG.debug("ConfigSpace: %s", self._config_space)
        return self._config_space

    @property
    def name(self) -> str:
        """
        The name of the optimizer.

        We save this information in mlos_bench storage to track the source of each
        configuration.
        """
        return self.__class__.__name__

    @property
    def targets(self) -> dict[str, Literal["min", "max"]]:
        """Returns a dictionary of optimization targets and their direction."""
        return {
            opt_target: "min" if opt_dir == 1 else "max"
            for (opt_target, opt_dir) in self._opt_targets.items()
        }

    @property
    def supports_preload(self) -> bool:
        """Return True if the optimizer supports pre-loading the data from previous
        experiments.
        """
        return True

    @abstractmethod
    def bulk_register(
        self,
        configs: Sequence[dict],
        scores: Sequence[dict[str, TunableValue] | None],
        status: Sequence[Status] | None = None,
    ) -> bool:
        """
        Pre-load the optimizer with the bulk data from previous experiments.

        Parameters
        ----------
        configs : Sequence[dict]
            Records of tunable values from other experiments.
        scores : Sequence[Optional[dict[str, TunableValue]]]
            Benchmark results from experiments that correspond to `configs`.
        status : Optional[Sequence[Status]]
            Status of the experiments that correspond to `configs`.

        Returns
        -------
        is_not_empty : bool
            True if there is data to register, false otherwise.
        """
        _LOG.info(
            "Update the optimizer with: %d configs, %d scores, %d status values",
            len(configs or []),
            len(scores or []),
            len(status or []),
        )
        if len(configs or []) != len(scores or []):
            raise ValueError("Numbers of configs and scores do not match.")
        if status is not None and len(configs or []) != len(status or []):
            raise ValueError("Numbers of configs and status values do not match.")
        has_data = bool(configs and scores)
        if has_data and self._start_with_defaults:
            _LOG.info("Prior data exists - do *NOT* use the default initialization.")
            self._start_with_defaults = False
        return has_data

    def suggest(self) -> TunableGroups:
        """
        Generate the next suggestion. Base class' implementation increments the
        iteration count and returns the current values of the tunables.

        Returns
        -------
        tunables : TunableGroups
            The next configuration to benchmark.
            These are the same tunables we pass to the constructor,
            but with the values set to the next suggestion.
        """
        self._iter += 1
        _LOG.debug("Iteration %d :: Suggest", self._iter)
        return self._tunables.copy()

    @abstractmethod
    def register(
        self,
        tunables: TunableGroups,
        status: Status,
        score: dict[str, TunableValue] | None = None,
    ) -> dict[str, float] | None:
        """
        Register the observation for the given configuration.

        Parameters
        ----------
        tunables : TunableGroups
            The configuration that has been benchmarked.
            Usually it's the same config that the `.suggest()` method returned.
        status : Status
            Final status of the experiment (e.g., SUCCEEDED or FAILED).
        score : Optional[dict[str, TunableValue]]
            A dict with the final benchmark results.
            None if the experiment was not successful.

        Returns
        -------
        value : Optional[dict[str, float]]
            Benchmark scores extracted (and possibly transformed)
            from the dataframe that's being MINIMIZED.
        """
        _LOG.info(
            "Iteration %d :: Register: %s = %s score: %s",
            self._iter,
            tunables,
            status,
            score,
        )
        if status.is_succeeded() == (score is None):  # XOR
            raise ValueError("Status and score must be consistent.")
        # FIXME: should maximization problems return -score values to the user, or
        # keep that as an internal nuance.
        return self._get_scores(status, score)

    def _get_scores(
        self,
        status: Status,
        scores: dict[str, TunableValue] | dict[str, float] | None,
    ) -> dict[str, float] | None:
        """
        Extract a scalar benchmark score from the dataframe. Change the sign if we are
        maximizing.

        Parameters
        ----------
        status : Status
            Final status of the experiment (e.g., SUCCEEDED or FAILED).
        scores : Optional[dict[str, TunableValue]]
            A dict with the final benchmark results.
            None if the experiment was not successful.

        Returns
        -------
        score : Optional[dict[str, float]]
            An optional dict of benchmark scores to be used as targets for MINIMIZATION.
        """
        if not status.is_completed():
            return None

        if not status.is_succeeded():
            assert scores is None
            # TODO: Be more flexible with values used for failed trials (not just +inf).
            # Issue: https://github.com/microsoft/MLOS/issues/523
            return {opt_target: float("inf") for opt_target in self._opt_targets}

        assert scores is not None
        target_metrics: dict[str, float] = {}
        for opt_target, opt_dir in self._opt_targets.items():
            val = scores[opt_target]
            assert val is not None
            target_metrics[opt_target] = float(val) * opt_dir

        return target_metrics

    def not_converged(self) -> bool:
        """
        Return True if not converged, False otherwise.

        Base implementation just checks the iteration count.
        """
        return self._iter < self._max_suggestions

    @abstractmethod
    def get_best_observation(
        self,
    ) -> tuple[dict[str, float], TunableGroups] | tuple[None, None]:
        """
        Get the best observation so far.

        Returns
        -------
        (value, tunables) : tuple[dict[str, float], TunableGroups]
            The best value and the corresponding configuration.
            (None, None) if no successful observation has been registered yet.
        """
