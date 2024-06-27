#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the RandomOptimizer class.
"""

from typing import Optional
from warnings import warn

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

    def _register(self, *, configurations: pd.DataFrame, scores: pd.DataFrame,
                  context: Optional[pd.DataFrame] = None) -> None:
        """Registers the given configurations and scores.

        Doesn't do anything on the RandomOptimizer except storing configurations for logging.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        scores : pd.DataFrame
            Scores from running the configurations. The index is the same as the index of the configurations.

        context : None
            Not Yet Implemented.
        """
        if context is not None:
            warn(f"Not Implemented: Ignoring context {list(context.columns)}", UserWarning)
        # should we pop them from self.pending_observations?

    def _suggest(self, *, context: Optional[pd.DataFrame] = None) -> pd.DataFrame:
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
            warn(f"Not Implemented: Ignoring context {list(context.columns)}", UserWarning)
        return pd.DataFrame(dict(self.optimizer_parameter_space.sample_configuration()), index=[0])

    def register_pending(self, *, configurations: pd.DataFrame,
                         context: Optional[pd.DataFrame] = None) -> None:
        raise NotImplementedError()
        # self._pending_observations.append((configurations, context))
