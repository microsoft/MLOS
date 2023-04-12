#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the RandomOptimizer class.
"""

import pandas as pd

from mlos_core.optimizers.optimizer import BaseOptimizer


class RandomOptimizer(BaseOptimizer):
    """Optimizer class that produces random suggestions.
    Useful for baseline comparison against Bayesian optimizers.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.
    """

    def _register(self, configurations: pd.DataFrame, scores: pd.Series, context: pd.DataFrame = None):
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
        # should we pop them from self.pending_observations?

    def _suggest(self, context: pd.DataFrame = None):
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
            # not sure how that works here?
            raise NotImplementedError()
        return pd.DataFrame(self.optimizer_parameter_space.sample_configuration().get_dictionary(), index=[0])

    def register_pending(self, configurations: pd.DataFrame, context: pd.DataFrame = None):
        raise NotImplementedError()
        # self._pending_observations.append((configurations, context))
