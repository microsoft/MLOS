#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import random

import pandas as pd
import numpy as np

from mlos.Optimizers.OptimizationProblem import SeriesObjective
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Spaces import Dimension, Hypergrid, Point, SimpleHypergrid
from mlos.Spaces.HypergridAdapters import HierarchicalToFlatHypergridAdapter
from mlos.Tracer import trace
from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.RegressionModels.DecisionTreeRegressionModel import DecisionTreeRegressionModel
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestConfigStore import homogeneous_random_forest_config_store
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestFitState import HomogeneousRandomForestFitState
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel


class SeriesAwareHomogeneousRandomForestRegressionModel(HomogeneousRandomForestRegressionModel):
    """TODO ZACK COMMENT
    """


    @trace()
    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            objective: SeriesObjective,
            logger=None
    ):
        if logger is None:
            logger = create_logger("SeriesAwareHomogeneousRandomForestRegressionModel")
        self.logger = logger

        assert model_config in homogeneous_random_forest_config_store.parameter_space

        self.objective = objective

        print("ZACK KAPPA")
        # If this is a series objective, create a fake set of forests
        #
        input_space_shallow_copy = SimpleHypergrid(
            name=input_space.name,
            dimensions=input_space.dimensions
        )
        series_modulation_dimension_copy = self.objective.series_modulation_dimension.copy()
        #series_modulation_dimension_copy.name = f"context_space.{series_modulation_dimension_copy.name}"
        #input_space_shallow_copy.add_dimension(series_modulation_dimension_copy)

        output_space_shallow_copy = SimpleHypergrid(
            name=output_space.name,
            dimensions=[self.objective.series_output_dimension]
        )

        HomogeneousRandomForestRegressionModel.__init__(
            self,
            model_config=model_config,
            input_space=input_space_shallow_copy,
            output_space=output_space_shallow_copy,
            logger=self.logger
        )
        print("CREATED RANDOM FOREST")
        print(self.input_space)
        print(self.output_space)

    @trace()
    def fit(self, feature_values_pandas_frame, target_values_pandas_frame, iteration_number):
        print("FITTING RANDOM FOREST")
        print("INPUT")
        print(feature_values_pandas_frame)
        print("TARGET VALUES")
        print(target_values_pandas_frame)

        HomogeneousRandomForestRegressionModel.fit(self, feature_values_pandas_frame, target_values_pandas_frame, iteration_number)

    @trace()
    def predict(self, feature_values_pandas_frame, include_only_valid_rows=True):
        """ Aggregate predictions from all estimators

        see: https://arxiv.org/pdf/1211.0906.pdf
        section: 4.3.2 for details

        :param feature_values_pandas_frame:
        :return: Prediction
"""

        self.logger.debug(f"Computing utility values for {len(feature_values_pandas_frame.index)} points.")

        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        del feature_values_pandas_frame[f"context_space.{self.objective.series_modulation_dimension.name}"]
        series_vals_df = pd.DataFrame({
            f"context_space.{self.objective.series_modulation_dimension.name}": self.objective.series_modulation_dimension.linspace()
        })
        feature_values_pandas_frame_merged = feature_values_pandas_frame.merge(series_vals_df, how="cross")
        print("INPUT")
        print(feature_values_pandas_frame_merged)

        raw_predictions = HomogeneousRandomForestRegressionModel.predict(self, feature_values_pandas_frame=feature_values_pandas_frame_merged)

        print(raw_predictions)
        predictions_df = raw_predictions.get_dataframe()
        print("OUTPUT")
        print(predictions_df)

        # TODO ZACK: Vectorize this. I'm sure pandas/numpy can do this faster. @Adam, any suggestions?
        utility_function_values = []
        variances = []
        current_e = []
        current_v = []
        for index, prediction in predictions_df.iterrows():
            current_e.append(prediction[predicted_value_col])
            current_v.append(prediction[predicted_value_var_col])
            if ((index + 1) % len(self.objective.series_modulation_dimension)) == 0:
                current_expected = np.array(current_e)
                current_variance = np.array(current_v)
                current_expected_minus_target = current_expected - self.objective.target_series
                calculated_utility_expectation = sum(current_expected_minus_target ** 2 + current_variance)
                calculated_utility_variance = \
                    sum(current_expected_minus_target ** 4 + 6 * (current_expected_minus_target ** 2) * current_variance
                        + 3 * current_variance ** 2 - (current_expected_minus_target ** 2 + current_variance) ** 2)
                utility_function_values.append(calculated_utility_expectation)
                variances.append(calculated_utility_variance)
                current_e = []
                current_v = []

        utility_function_values = pd.to_numeric(arg=utility_function_values, errors='raise')
        utility_df = pd.DataFrame({"u":utility_function_values, "v":variances}, index=feature_values_pandas_frame.index,
                                  dtype='float')
        print("ZACK")
        print(utility_df)
        return utility_df
