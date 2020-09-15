#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod
from typing import Dict, Tuple

import pandas as pd

from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import Point

class OptimizerBase(ABC):
    """ Defines the interface to all our optimizers.

    """

    @abstractmethod
    def __init__(self, optimization_problem: OptimizationProblem):
        self.optimization_problem = optimization_problem
        self.optimizer_config = None # TODO: pass from subclasses.

    @abstractmethod
    def get_optimizer_convergence_state(self):
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def suggest(self, random=False, context=None) -> Point:
        """ Suggest the next set of parameters to try.

        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def register(self, feature_values_pandas_frame, target_values_pandas_frame) -> None:
        """ Registers a new result with the optimizer.

        :param params:
        :param target_value:
        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def get_all_observations(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def predict(self, feature_values_pandas_frame, t=None) -> Prediction:
        """ Predict target value based on the parameters supplied.

        :param params:
        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    def optimum(self, stay_focused=False) -> Dict: # pylint: disable=unused-argument  # TODO take context
        """ Return the optimal value found so far along with the related parameter values.

        This could be either min or max, depending on the settings.

        Returns
        -------
        best_config_point : Point
            Configuration that corresponds to the optimum objective value.
        best_objective : Point
            Best objective value observed so far.
        """
        features_df, objectives_df = self.get_all_observations()

        if self.optimization_problem.objectives[0].minimize:
            index_of_best_target = objectives_df.idxmin()[0]
        else:
            index_of_best_target = objectives_df.idxmax()[0]
        best_objective = Point.from_dataframe(objectives_df.loc[[index_of_best_target]])
        best_config_point = Point.from_dataframe(features_df.loc[[index_of_best_target]])


        return best_config_point, best_objective

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
