#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the wrapper classes for base Bayesian optimizers.
"""

from abc import ABCMeta, abstractmethod

from typing import Optional

import pandas as pd
import numpy.typing as npt

from mlos_core.optimizers.optimizer import BaseOptimizer


class BaseBayesianOptimizer(BaseOptimizer, metaclass=ABCMeta):
    """Abstract base class defining the interface for Bayesian optimization."""

    @abstractmethod
    def surrogate_predict(self, configurations: pd.DataFrame,
                          context: Optional[pd.DataFrame] = None) -> npt.NDArray:
        """Obtain a prediction from this Bayesian optimizer's surrogate model for the given configuration(s).

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        pass    # pylint: disable=unnecessary-pass # pragma: no cover

    @abstractmethod
    def acquisition_function(self, configurations: pd.DataFrame,
                             context: Optional[pd.DataFrame] = None) -> npt.NDArray:
        """Invokes the acquisition function from this Bayesian optimizer for the given configuration.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        pass    # pylint: disable=unnecessary-pass # pragma: no cover
