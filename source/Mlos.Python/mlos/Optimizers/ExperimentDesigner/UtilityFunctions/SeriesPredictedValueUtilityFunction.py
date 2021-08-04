#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
import pandas as pd
from scipy.stats import t
from mlos.Logger import create_logger
from mlos.Optimizers.OptimizationProblem import SeriesObjective
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.UtilityFunction import UtilityFunction
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, CategoricalDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore
from mlos.Tracer import trace


class SeriesPredictedValueUtilityFunction(UtilityFunction):
    def __init__(self, surrogate_model: MultiObjectiveRegressionModel, objective: SeriesObjective, logger=None):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.series_objective = objective
        self._sign = 1 if not self.series_objective.minimize else -1
        self.surrogate_model: MultiObjectiveRegressionModel = surrogate_model

    @trace()
    def __call__(self, feature_values_pandas_frame):
        # NOTE: THIS LOGIC IS DUPLICATED INTO SeriesPredictedValueUtilityFunction and SeriesDifferenceUtilityFunction.
        # Later they will diverge as SeriesDifferenceUtilityFunction should require additional logic surrounding probability
        # of improvement. Perhaps this part should be refactored to be shared though.
        #
        self.logger.debug(f"Computing utility values for {len(feature_values_pandas_frame.index)} points.")

        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        del feature_values_pandas_frame[f"context_space.{self.series_objective.series_modulation_dimension.name}"]
        series_vals_df = pd.DataFrame({
            f"context_space.{self.series_objective.series_modulation_dimension.name}": self.series_objective.series_modulation_dimension.linspace()
        })
        feature_values_pandas_frame_merged = feature_values_pandas_frame.merge(series_vals_df, how="cross")
        multi_objective_predictions = self.surrogate_model.predict(features_df=feature_values_pandas_frame_merged)

        predictions = multi_objective_predictions[0]
        predictions_df = predictions.get_dataframe()

        # TODO ZACK: Vectorize this. I'm sure pandas/numpy can do this faster. @Adam, any suggestions
        resulting_series_arry = []
        current_arry = []
        for index, prediction in predictions_df.iterrows():
            current_arry.append(prediction[predicted_value_col])
            if ((index + 1) % len(self.series_objective.series_modulation_dimension)) == 0:
                resulting_series_arry.append(np.array(current_arry))
                current_arry=[]

        # Didn't do bootstrapping yet because I think math would be computationally faster
        utility_function_values = []
        for series in resulting_series_arry:
            utility_function_values.append(self._sign * sum((self.series_objective.target_series-series)**2))

        utility_function_values = pd.to_numeric(arg=utility_function_values, errors='raise')
        utility_df = pd.DataFrame(data=utility_function_values, index=feature_values_pandas_frame.index, columns=['utility'], dtype='float')
        assert utility_df.dtypes['utility'] == float, f"{utility_df} has the wrong type for the 'utility' column: {utility_df.dtypes['utility']}"
        return utility_df
