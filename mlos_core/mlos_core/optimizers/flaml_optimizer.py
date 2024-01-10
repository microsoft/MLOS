#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the FlamlOptimizer class.
"""

from typing import Dict, NamedTuple, Optional, Union
from warnings import warn

import ConfigSpace
import numpy as np
import pandas as pd

from mlos_core.util import normalize_config
from mlos_core.optimizers.optimizer import BaseOptimizer
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter


class EvaluatedSample(NamedTuple):
    """A named tuple representing a sample that has been evaluated."""

    config: dict
    score: float


class FlamlOptimizer(BaseOptimizer):
    """Wrapper class for FLAML Optimizer: A fast library for AutoML and tuning.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.

    space_adapter : BaseSpaceAdapter
        The space adapter class to employ for parameter space transformations.

    low_cost_partial_config : dict
        A dictionary from a subset of controlled dimensions to the initial low-cost values.
        More info: https://microsoft.github.io/FLAML/docs/FAQ#about-low_cost_partial_config-in-tune

    seed : Optional[int]
        If provided, calls np.random.seed() with the provided value to set the seed globally at init.
    """

    def __init__(self, *,
                 parameter_space: ConfigSpace.ConfigurationSpace,
                 space_adapter: Optional[BaseSpaceAdapter] = None,
                 low_cost_partial_config: Optional[dict] = None,
                 seed: Optional[int] = None):

        super().__init__(
            parameter_space=parameter_space,
            space_adapter=space_adapter,
        )

        # Per upstream documentation, it is recommended to set the seed for
        # flaml at the start of its operation globally.
        if seed is not None:
            np.random.seed(seed)

        # pylint: disable=import-outside-toplevel
        from mlos_core.spaces.converters.flaml import configspace_to_flaml_space, FlamlDomain

        self.flaml_parameter_space: Dict[str, FlamlDomain] = configspace_to_flaml_space(self.optimizer_parameter_space)
        self.low_cost_partial_config = low_cost_partial_config

        self.evaluated_samples: Dict[ConfigSpace.Configuration, EvaluatedSample] = {}
        self._suggested_config: Optional[dict]

    def _register(self, configurations: pd.DataFrame, scores: pd.Series,
                  context: Optional[pd.DataFrame] = None) -> None:
        """Registers the given configurations and scores.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        scores : pd.Series
            Scores from running the configurations. The index is the same as the index of the configurations.

        context : None
            Not Yet Implemented.
        """
        if context is not None:
            raise NotImplementedError()
        for (_, config), score in zip(configurations.iterrows(), scores):
            cs_config: ConfigSpace.Configuration = ConfigSpace.Configuration(
                self.optimizer_parameter_space, values=config.to_dict())
            if cs_config in self.evaluated_samples:
                warn(f"Configuration {config} was already registered", UserWarning)

            self.evaluated_samples[cs_config] = EvaluatedSample(config=config.to_dict(), score=score)

    def _suggest(self, context: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Suggests a new configuration.

        Sampled at random using ConfigSpace.

        Parameters
        ----------
        context : None
            Not Yet Implemented.

        Returns
        -------
        configuration : pd.DataFrame
            Pandas dataframe with a single row. Column names are the parameter names.
        """
        if context is not None:
            raise NotImplementedError()
        config: dict = self._get_next_config()
        return pd.DataFrame(config, index=[0])

    def register_pending(self, configurations: pd.DataFrame,
                         context: Optional[pd.DataFrame] = None) -> None:
        raise NotImplementedError()

    def _target_function(self, config: dict) -> Union[dict, None]:
        """Configuration evaluation function called by FLAML optimizer.

        FLAML may suggest the same configuration multiple times (due to its warm-start mechanism).
        Once FLAML suggests an unseen configuration, we store it, and stop the optimization process.

        Parameters
        ----------
        config: dict
            Next configuration to be evaluated, as suggested by FLAML.
            This config is stored internally and is returned to user, via `.suggest()` method.

        Returns
        -------
        result: Union[dict, None]
            Dictionary with a single key, `score`, if config already evaluated; `None` otherwise.
        """
        cs_config = normalize_config(self.optimizer_parameter_space, config)
        if cs_config in self.evaluated_samples:
            return {'score': self.evaluated_samples[cs_config].score}

        self._suggested_config = dict(cs_config)  # Cleaned-up version of the config
        return None  # Returning None stops the process

    def _get_next_config(self) -> dict:
        """Warm-starts a new instance of FLAML, and returns a recommended, unseen new configuration.

        Since FLAML does not provide an ask-and-tell interface, we need to create a new instance of FLAML
        each time we get asked for a new suggestion. This is suboptimal performance-wise, but works.
        To do so, we use any previously evaluated configurations to bootstrap FLAML (i.e., warm-start).
        For more info: https://microsoft.github.io/FLAML/docs/Use-Cases/Tune-User-Defined-Function#warm-start

        Returns
        -------
        result: dict
            Dictionary with a single key, `score`, if config already evaluated; `None` otherwise.

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
            evaluated_rewards = [
                s.score for s in self.evaluated_samples.values()
            ]

        # Warm start FLAML optimizer
        self._suggested_config = None
        tune.run(
            self._target_function,
            config=self.flaml_parameter_space,
            mode='min',
            metric='score',
            points_to_evaluate=points_to_evaluate,
            evaluated_rewards=evaluated_rewards,
            num_samples=len(points_to_evaluate) + 1,
            low_cost_partial_config=self.low_cost_partial_config,
            verbose=0,
        )
        if self._suggested_config is None:
            raise RuntimeError('FLAML did not produce a suggestion')

        return self._suggested_config  # type: ignore[unreachable]
