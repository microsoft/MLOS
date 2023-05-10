#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the FlamlOptimizer class.
"""

from typing import Dict, Optional
from warnings import warn

import ConfigSpace
import pandas as pd

from mlos_core.optimizers.optimizer import BaseOptimizer
from mlos_core.spaces import configspace_to_flaml_space
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter


class FlamlOptimizer(BaseOptimizer):
    """Optimizer class that produces random suggestions.
    Useful for baseline comparison against Bayesian optimizers.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.
    """

    def __init__(
        self,
        parameter_space: ConfigSpace.ConfigurationSpace,
        space_adapter: Optional[BaseSpaceAdapter] = None,
    ):
        super().__init__(parameter_space, space_adapter)
        self.flaml_parameter_space: dict = configspace_to_flaml_space(self.optimizer_parameter_space)
        self.evaluated_configs: Dict[int, dict] = {}
        self._suggested_config: Optional[dict]

    def _register(self, configurations: pd.DataFrame, scores: pd.Series,
                  context: Optional[pd.DataFrame] = None) -> None:
        """Registers the given configurations and scores.

        Doesn't do anything on the RandomOptimizer except storing configurations for logging.

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
            config_hash: int = hash(ConfigSpace.Configuration(self.optimizer_parameter_space, values=config.to_dict()))
            if config_hash in self.evaluated_configs:
                warn(f"Configuration {config} was already registered", UserWarning)

            self.evaluated_configs[config_hash] = {
                'config': config.to_dict(),
                'score': score,
            }

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

    def _target_function(self, config: dict) -> None:
        config_hash: int = hash(ConfigSpace.Configuration(self.optimizer_parameter_space, values=config))
        if config_hash in self.evaluated_configs:
            score = self.evaluated_configs[config_hash]['score']
            return {'score': score}

        self._suggested_config = config
        return None  # Returning None stops the process

    def _get_next_config(self) -> dict:
        from flaml import tune  # pylint: disable=import-outside-toplevel

        # Parse evaluated configs to format used by FLAML
        points_to_evaluate: list = []
        evaluated_rewards: list = []
        if len(self.evaluated_configs) > 0:
            evaluated_configs_list: list = [(d['config'], d['score']) for d in self.evaluated_configs.values()]
            points_to_evaluate, evaluated_rewards = list(zip(*evaluated_configs_list))

        # Warm start FLAML optimizer
        self._suggested_config = None
        _ = tune.run(
            self._target_function,
            config=self.flaml_parameter_space,
            mode='min',
            metric='score',
            points_to_evaluate=list(points_to_evaluate),
            evaluated_rewards=list(evaluated_rewards),
            num_samples=len(points_to_evaluate) + 1,
            verbose=0,
        )
        if self._suggested_config is None:
            raise RuntimeError('FLAML did not produce a suggestion')

        return self._suggested_config
