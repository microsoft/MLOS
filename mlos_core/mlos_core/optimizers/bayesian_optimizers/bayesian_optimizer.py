#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the wrapper classes for base Bayesian optimizers.
"""

from abc import ABCMeta, abstractmethod

from typing import Callable, Optional

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

    def acquisition_function(self, configurations: pd.DataFrame,
                             context: Optional[pd.DataFrame] = None) -> Callable:
        """Invokes the acquisition function from this Bayesian optimizer for the given configuration.

        Default implementation throws NotImplementedError.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        raise NotImplementedError()
