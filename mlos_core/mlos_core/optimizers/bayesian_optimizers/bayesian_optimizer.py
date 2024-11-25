#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Contains the wrapper classes for base Bayesian optimizers."""

from abc import ABCMeta, abstractmethod

import numpy.typing as npt

from mlos_core.data_classes import Suggestion
from mlos_core.optimizers.optimizer import BaseOptimizer


class BaseBayesianOptimizer(BaseOptimizer, metaclass=ABCMeta):
    """Abstract base class defining the interface for Bayesian optimization."""

    @abstractmethod
    def surrogate_predict(self, suggestion: Suggestion) -> npt.NDArray:
        """
        Obtain a prediction from this Bayesian optimizer's surrogate model for the given
        configuration(s).

        Parameters
        ----------
        suggestion: Suggestion
            The suggestion containing the configuration(s) to predict.
        """
        pass  # pylint: disable=unnecessary-pass # pragma: no cover

    @abstractmethod
    def acquisition_function(self, suggestion: Suggestion) -> npt.NDArray:
        """
        Invokes the acquisition function from this Bayesian optimizer for the given
        configuration.

        Parameters
        ----------
        suggestion: Suggestion
            The suggestion containing the configuration(s) to evaluate.
        """
        pass  # pylint: disable=unnecessary-pass # pragma: no cover
