#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from scipy.stats import t

from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import GoodnessOfFitMetrics, DataSetType
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.RegressionModels.RegressionModelFitState import RegressionModelFitState
from mlos.Spaces import Hypergrid
from mlos.Tracer import trace


class RegressionModel(ABC):
    """ An abstract class for all regression models to implement.

    The purpose of this class is to indicate the type and configuration of the regression model
    so that all models can be inspected in a homogeneous way.
    """

    @abstractmethod
    def __init__(self, model_type, model_config, input_space: Hypergrid, output_space: Hypergrid, fit_state: RegressionModelFitState = None):
        self.model_type = model_type
        self.model_config = model_config
        self.input_space = input_space
        self.output_space = output_space
        self.input_dimension_names = None
        self.target_dimension_names = self.target_dimension_names = [dimension.name for dimension in self.output_space.dimensions]
        self.fit_state = fit_state if fit_state is not None else RegressionModelFitState()
        self.last_refit_iteration_number = 0  # Every time we refit, we update this. It serves as a version number.

    @property
    @abstractmethod
    def trained(self):
        raise NotImplementedError

    @abstractmethod
    def fit(self, feature_values_pandas_frame, target_values_pandas_frame, iteration_number):
        raise NotImplementedError

    @abstractmethod
    def predict(self, feature_values_pandas_frame, include_only_valid_rows=True):
        raise NotImplementedError

    @trace()
    def compute_goodness_of_fit(self, features_df: pd.DataFrame, target_df: pd.DataFrame, data_set_type: DataSetType):

        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        sample_var_col = Prediction.LegalColumnNames.SAMPLE_VARIANCE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        predictions = self.predict(features_df.copy()) # TODO: remove the copy
        predictions_df = predictions.get_dataframe()
        num_predictions = len(predictions_df.index)

        mean_absolute_error = None
        root_mean_squared_error = None
        relative_absolute_error = None
        relative_squared_error = None
        coefficient_of_determination = None
        prediction_90_ci_hit_rate = None
        sample_90_ci_hit_rate = None

        if num_predictions > 0:
            target_value = target_df.loc[predictions_df.index, self.target_dimension_names[0]]
            target_mean = target_value.mean()
            absolute_target_variation = (target_value - target_mean).abs()
            squared_target_variation = absolute_target_variation ** 2
            sum_absolute_target_variation = absolute_target_variation.sum()
            sum_squared_target_variation = squared_target_variation.sum()  # a.k.a.: total sum of squares
            error = target_value - predictions_df[predicted_value_col]
            absolute_error = error.abs()
            squared_error = error ** 2
            sum_absolute_error = absolute_error.sum()
            sum_squared_error = squared_error.sum()  # a.k.a.: residal sum of squares

            mean_absolute_error = sum_absolute_error / num_predictions
            root_mean_squared_error = np.sqrt(sum_squared_error / num_predictions)
            if sum_absolute_target_variation > 0:
                relative_absolute_error = sum_absolute_error / sum_absolute_target_variation
                relative_squared_error = np.sqrt(sum_squared_error / sum_squared_target_variation)
                coefficient_of_determination = 1 - (sum_squared_error/sum_squared_target_variation)

            # TODO: Ask Ed about which degrees of freedom to use here...
            # adjusted_coefficient_of_determination = ...

            if not (predictions_df[dof_col] == 0).any():
                t_values_90_percent = t.ppf(0.95, predictions_df[dof_col])
                # t_values_95_percent = t.ppf(0.975, predictions_df[dof_col])
                # t_values_99_percent = t.ppf(0.995, predictions_df[dof_col])
                prediction_90_ci_radius = t_values_90_percent * np.sqrt(predictions_df[predicted_value_var_col])

                if sample_var_col in predictions_df.columns.values:
                    sample_90_ci_radius = t_values_90_percent * np.sqrt(predictions_df[sample_var_col])
                    sample_90_ci_hit_rate = (absolute_error < sample_90_ci_radius).mean()
                prediction_90_ci_hit_rate = (absolute_error < prediction_90_ci_radius).mean()

        gof_metrics = GoodnessOfFitMetrics(
            last_refit_iteration_number=self.last_refit_iteration_number,
            observation_count=len(features_df.index),
            prediction_count=len(predictions_df.index),
            data_set_type=data_set_type,
            mean_absolute_error=mean_absolute_error,
            root_mean_squared_error=root_mean_squared_error,
            relative_absolute_error=relative_absolute_error,
            relative_squared_error=relative_squared_error,
            coefficient_of_determination=coefficient_of_determination,
            # adjusted_coefficient_of_determination=None,
            prediction_90_ci_hit_rate=prediction_90_ci_hit_rate,
            # prediction_95_ci_hit_rate=None,
            # prediction_99_ci_hit_rate=None,
            sample_90_ci_hit_rate=sample_90_ci_hit_rate,
            # sample_95_ci_hit_rate=None,
            # sample_99_ci_hit_rate=None,
        )
        return gof_metrics
