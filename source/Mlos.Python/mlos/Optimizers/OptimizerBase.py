#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np
import pandas as pd
import scipy.stats

from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.OptimumDefinition import OptimumDefinition
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import Point
from mlos.Tracer import trace

class OptimizerBase(ABC):
    """Defines the base class to all our optimizers.

    """

    @abstractmethod
    def __init__(self, optimization_problem: OptimizationProblem):
        self.optimization_problem = optimization_problem
        self.optimizer_config = None # TODO: pass from subclasses.

    @property
    def trained(self):
        raise NotImplementedError

    @abstractmethod
    def compute_surrogate_model_goodness_of_fit(self):
        raise NotImplementedError

    @abstractmethod
    def get_optimizer_convergence_state(self):
        raise NotImplementedError("All subclasses must implement this method.")

    def get_surrogate_model_fit_state(self):
        return self.get_optimizer_convergence_state().surrogate_model_fit_state

    @abstractmethod
    def suggest(self, random=False, context=None) -> Point:
        """Suggest the next set of parameters to try.

        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def register(self, feature_values_pandas_frame, target_values_pandas_frame) -> None:
        """Registers a new result with the optimizer.

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
        """Predict target value based on the parameters supplied.

        :param params:
        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    def optimum(self, optimum_definition: OptimumDefinition = OptimumDefinition.BEST_OBSERVATION, alpha: float = 0.05) -> Tuple[Point, Point]:
        """Return the optimal value found so far along with the related parameter values.

        This could be either min or max, depending on the settings.

        Returns
        -------
        best_config_point : Point
            Configuration that corresponds to the optimum objective value.

        best_objective_point : Point
            Best optimum value as specified by the OptimumDefinition argument (corresponding to the best_config_point).

        """
        assert optimum_definition in OptimumDefinition

        features_df, objectives_df = self.get_all_observations()
        if not len(features_df.index):
            raise ValueError("Can't compute optimum before registering any observations.")

        if optimum_definition == OptimumDefinition.BEST_OBSERVATION:
            return self._best_observation_optimum(features_df=features_df, objectives_df=objectives_df)
        return self._prediction_based_optimum(features_df=features_df, optimum_definition=optimum_definition, alpha=alpha)


    @trace()
    def _best_observation_optimum(self, features_df: pd.DataFrame, objectives_df: pd.DataFrame) -> Tuple[Point, Point]:
        objective = self.optimization_problem.objectives[0]
        if objective.minimize:
            index_of_best = objectives_df[objective.name].idxmin()
        else:
            index_of_best = objectives_df[objective.name].idxmax()
        optimum_value = Point.from_dataframe(objectives_df.loc[[index_of_best]])
        config_at_optimum = Point.from_dataframe(features_df.loc[[index_of_best]])
        return config_at_optimum, optimum_value

    @trace()
    def _prediction_based_optimum(self, features_df: pd.DataFrame, optimum_definition: OptimumDefinition, alpha: float)-> Tuple[Point, Point]:
        objective = self.optimization_problem.objectives[0]

        predictions = self.predict(feature_values_pandas_frame=features_df)
        predictions_df = predictions.get_dataframe()

        if len(predictions_df.index) == 0:
            raise ValueError("Insufficient data to compute confidence-bound based optimum.")

        # Predictions index must be a subset of features index.
        #
        assert features_df.index.intersection(predictions_df.index).equals(predictions_df.index)

        predicted_value_column_name = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        dof_column_name = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value
        variance_column_name = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value

        if optimum_definition == OptimumDefinition.PREDICTED_VALUE_FOR_OBSERVED_CONFIG:
            if objective.minimize:
                index_of_best = predictions_df[predicted_value_column_name].idxmin()
            else:
                index_of_best = predictions_df[predicted_value_column_name].idxmax()

            optimum_value = Point.from_dataframe(predictions_df.loc[[index_of_best], [predicted_value_column_name]])

        else:
            # We will be manipulating this data so let's make a copy for now.
            # TODO: Profile this and if necessary optimize this copy away.
            #
            predictions_df = predictions_df.copy(deep=True)

            # Drop nulls and zeroes.
            #
            predictions_df = predictions_df[predictions_df[dof_column_name].notna() & (predictions_df[dof_column_name] != 0)]

            if len(predictions_df.index) == 0:
                raise ValueError("Insufficient data to compute confidence-bound based optimum.")

            t_values = scipy.stats.t.ppf(1 - alpha / 2, predictions_df[dof_column_name])
            prediction_interval_radii = t_values * np.sqrt(predictions_df[variance_column_name])

            if optimum_definition == OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG:
                upper_confidence_bounds = predictions_df[predicted_value_column_name] + prediction_interval_radii
                if objective.minimize:
                    index_of_best = upper_confidence_bounds.idxmin()
                else:
                    index_of_best = upper_confidence_bounds.idxmax()
                optimum_value = Point(upper_confidence_bound=upper_confidence_bounds.loc[index_of_best])
            elif optimum_definition == OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG:
                lower_confidence_bounds = predictions_df[predicted_value_column_name] - prediction_interval_radii
                if objective.minimize:
                    index_of_best = lower_confidence_bounds.idxmin()
                else:
                    index_of_best = lower_confidence_bounds.idxmax()
                optimum_value = Point(lower_confidence_bound=lower_confidence_bounds.loc[index_of_best])
            else:
                raise RuntimeError(f"Unknown optimum definition.")

        config_at_optimum = Point.from_dataframe(features_df.loc[[index_of_best]])
        return config_at_optimum, optimum_value

    @abstractmethod
    def focus(self, subspace):
        """Force the optimizer to focus on a specific subspace.

        This could be a great way to pass priors to the optimizer, as well as play with the component for the developers.

        :param subspace:
        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")

    @abstractmethod
    def reset_focus(self):
        """Changes focus back to the full search space.

        :return:
        """
        raise NotImplementedError("All subclasses must implement this method.")
