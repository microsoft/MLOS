#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the :py:class:`.FlamlOptimizer` class.

Notes
-----
See the `Flaml Documentation <https://microsoft.github.io/FLAML/>`_ for more
details.
"""

from typing import NamedTuple
from warnings import warn

import ConfigSpace
import numpy as np
import pandas as pd

from mlos_core.data_classes import Observation, Observations, Suggestion
from mlos_core.optimizers.optimizer import BaseOptimizer
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter
from mlos_core.util import normalize_config


class EvaluatedSample(NamedTuple):
    """A named tuple representing a sample that has been evaluated."""

    config: dict
    score: float


class FlamlOptimizer(BaseOptimizer):
    """Wrapper class for FLAML Optimizer: A fast library for AutoML and tuning."""

    # The name of an internal objective attribute that is calculated as a weighted
    # average of the user provided objective metrics.
    _METRIC_NAME = "FLAML_score"

    def __init__(
        self,
        *,  # pylint: disable=too-many-arguments
        parameter_space: ConfigSpace.ConfigurationSpace,
        optimization_targets: list[str],
        objective_weights: list[float] | None = None,
        space_adapter: BaseSpaceAdapter | None = None,
        low_cost_partial_config: dict | None = None,
        seed: int | None = None,
    ):
        """
        Create an MLOS wrapper for FLAML.

        Parameters
        ----------
        parameter_space : ConfigSpace.ConfigurationSpace
            The parameter space to optimize.

        optimization_targets : list[str]
            The names of the optimization targets to minimize.

        objective_weights : Optional[list[float]]
            Optional list of weights of optimization targets.

        space_adapter : BaseSpaceAdapter
            The space adapter class to employ for parameter space transformations.

        low_cost_partial_config : dict
            A dictionary from a subset of controlled dimensions to the initial low-cost values.
            More info:
            https://microsoft.github.io/FLAML/docs/FAQ#about-low_cost_partial_config-in-tune

        seed : int | None
            If provided, calls np.random.seed() with the provided value to set the
            seed globally at init.
        """
        super().__init__(
            parameter_space=parameter_space,
            optimization_targets=optimization_targets,
            objective_weights=objective_weights,
            space_adapter=space_adapter,
        )

        # Per upstream documentation, it is recommended to set the seed for
        # flaml at the start of its operation globally.
        if seed is not None:
            np.random.seed(seed)

        # pylint: disable=import-outside-toplevel
        from mlos_core.spaces.converters.flaml import (
            FlamlDomain,
            configspace_to_flaml_space,
        )

        self.flaml_parameter_space: dict[str, FlamlDomain] = configspace_to_flaml_space(
            self.optimizer_parameter_space
        )
        self.low_cost_partial_config = low_cost_partial_config

        self.evaluated_samples: dict[ConfigSpace.Configuration, EvaluatedSample] = {}
        self._suggested_config: dict | None

    def _register(
        self,
        observations: Observations,
    ) -> None:
        """
        Registers one or more configs/score pairs (observations) with the underlying
        optimizer.

        Parameters
        ----------
        observations : Observations
            The set of config/scores to register.
        """
        # TODO: Implement bulk registration.
        # (e.g., by rebuilding the base optimizer instance with all observations).
        for observation in observations:
            self._register_single(observation)

    def _register_single(
        self,
        observation: Observation,
    ) -> None:
        """
        Registers the given config and its score.

        Parameters
        ----------
        observation : Observation
            The observation to register.
        """
        if observation.context is not None:
            warn(
                f"Not Implemented: Ignoring context {list(observation.context.index)}",
                UserWarning,
            )
        if observation.metadata is not None:
            warn(
                f"Not Implemented: Ignoring metadata {list(observation.metadata.index)}",
                UserWarning,
            )

        cs_config: ConfigSpace.Configuration = observation.to_suggestion().to_configspace_config(
            self.optimizer_parameter_space
        )
        if cs_config in self.evaluated_samples:
            warn(f"Configuration {cs_config} was already registered", UserWarning)
        self.evaluated_samples[cs_config] = EvaluatedSample(
            config=dict(cs_config),
            score=float(
                np.average(observation.score.astype(float), weights=self._objective_weights)
            ),
        )

    def _suggest(
        self,
        *,
        context: pd.Series | None = None,
    ) -> Suggestion:
        """
        Suggests a new configuration.

        Sampled at random using ConfigSpace.

        Parameters
        ----------
        context : None
            Not Yet Implemented.

        Returns
        -------
        suggestion : Suggestion
            The suggestion to be evaluated.
        """
        if context is not None:
            warn(f"Not Implemented: Ignoring context {list(context.index)}", UserWarning)
        config: dict = self._get_next_config()
        return Suggestion(config=pd.Series(config, dtype=object), context=context, metadata=None)

    def register_pending(self, pending: Suggestion) -> None:
        raise NotImplementedError()

    def _target_function(self, config: dict) -> dict | None:
        """
        Configuration evaluation function called by FLAML optimizer.

        FLAML may suggest the same configuration multiple times (due to its
        warm-start mechanism).  Once FLAML suggests an unseen configuration, we
        store it, and stop the optimization process.

        Parameters
        ----------
        config: dict
            Next configuration to be evaluated, as suggested by FLAML.
            This config is stored internally and is returned to user, via
            `.suggest()` method.

        Returns
        -------
        result: dict | None
            Dictionary with a single key, `FLAML_score`, if config already
            evaluated; `None` otherwise.
        """
        cs_config = normalize_config(self.optimizer_parameter_space, config)
        if cs_config in self.evaluated_samples:
            return {self._METRIC_NAME: self.evaluated_samples[cs_config].score}

        self._suggested_config = dict(cs_config)  # Cleaned-up version of the config
        return None  # Returning None stops the process

    def _get_next_config(self) -> dict:
        """
        Warm-starts a new instance of FLAML, and returns a recommended, unseen new
        configuration.

        Since FLAML does not provide an ask-and-tell interface, we need to create a
        new instance of FLAML each time we get asked for a new suggestion. This is
        suboptimal performance-wise, but works.
        To do so, we use any previously evaluated configs to bootstrap FLAML (i.e.,
        warm-start).
        For more info:
        https://microsoft.github.io/FLAML/docs/Use-Cases/Tune-User-Defined-Function#warm-start

        Returns
        -------
        result: dict
            A dictionary with a single key that is equal to the name of the optimization target,
            if config already evaluated; `None` otherwise.

        Raises
        ------
        RuntimeError: if FLAML did not suggest a previously unseen configuration.
        """
        from flaml import tune  # pylint: disable=import-outside-toplevel

        # Parse evaluated configs to format used by FLAML
        points_to_evaluate: list = []
        evaluated_rewards: list = []
        if len(self.evaluated_samples) > 0:
            points_to_evaluate = [
                dict(normalize_config(self.optimizer_parameter_space, conf))
                for conf in self.evaluated_samples
            ]
            evaluated_rewards = [s.score for s in self.evaluated_samples.values()]

        # Warm start FLAML optimizer
        self._suggested_config = None
        tune.run(
            self._target_function,
            config=self.flaml_parameter_space,
            mode="min",
            metric=self._METRIC_NAME,
            points_to_evaluate=points_to_evaluate,
            evaluated_rewards=evaluated_rewards,
            num_samples=len(points_to_evaluate) + 1,
            low_cost_partial_config=self.low_cost_partial_config,
            verbose=0,
        )
        if self._suggested_config is None:
            raise RuntimeError("FLAML did not produce a suggestion")

        return self._suggested_config  # type: ignore[unreachable]
