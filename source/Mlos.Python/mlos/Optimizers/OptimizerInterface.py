#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod

from .OptimizationProblem import OptimizationProblem

class OptimizerInterface(ABC):
    """ Defines the interface to all our optimizers.

    """

    @abstractmethod
    def __init__(self, optimization_problem: OptimizationProblem):
        self.optimization_problem = optimization_problem

    @abstractmethod
    def suggest(self, random=False, context=None):
        """ Suggest the next set of parameters to try.

        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def register(self, feature_values_pandas_frame, target_values_pandas_frame):
        """ Registers a new result with the optimizer.

        :param params:
        :param target_value:
        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def predict(self, feature_values_pandas_frame, t=None):
        """ Predict target value based on the parameters supplied.

        :param params:
        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def optimum(self, stay_focused=False):
        """ Return the optimal value found so far along with the related parameter values.

        This could be either min or max, depending on the settings.

        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def focus(self, subspace):
        """ Force the optimizer to focus on a specific subspace.

        This could be a great way to pass priors to the optimizer, as well as play with the component for the developers.

        :param subspace:
        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def reset_focus(self):
        """ Changes focus back to the full search space.

        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")
