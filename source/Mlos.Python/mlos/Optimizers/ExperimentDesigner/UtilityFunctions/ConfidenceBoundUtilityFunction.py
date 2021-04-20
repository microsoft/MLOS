#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
import pandas as pd
from scipy.stats import t
from mlos.Logger import create_logger
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.UtilityFunction import UtilityFunction
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, CategoricalDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore
from mlos.Tracer import trace


confidence_bound_utility_function_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="confidence_bound_utility_function_config",
        dimensions=[
            CategoricalDimension(name="utility_function_name", values=["lower_confidence_bound_on_improvement", "upper_confidence_bound_on_improvement"]),
            ContinuousDimension(name="alpha", min=0.01, max=0.5)
        ]
    ),
    default=Point(
        utility_function_name="upper_confidence_bound_on_improvement",
        alpha=0.01
    )
)


class ConfidenceBoundUtilityFunction(UtilityFunction):
    def __init__(self, function_config: Point, surrogate_model: MultiObjectiveRegressionModel, minimize: bool, logger=None):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.config = function_config
        self.minimize = minimize
        self._sign = 1 if not minimize else -1
        if self.config.utility_function_name not in ("lower_confidence_bound_on_improvement", "upper_confidence_bound_on_improvement"):
            raise RuntimeError(f"Invalid utility function name: {self.config.utility_function_name}.")

        self.surrogate_model: MultiObjectiveRegressionModel = surrogate_model

    @trace()
    def __call__(self, feature_values_pandas_frame):
        self.logger.debug(f"Computing utility values for {len(feature_values_pandas_frame.index)} points.")

        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        multi_objective_predictions = self.surrogate_model.predict(features_df=feature_values_pandas_frame)

        # While the models can predict multiple objectives, here we just compute the utility for the first one. Next-steps include:
        #   1. Select the objective by name
        #   2. Write multi-objective utility functions
        #
        # But for now, the behavior below keeps the behavior of the optimizer unchanged.
        #
        predictions = multi_objective_predictions[0]
        predictions_df = predictions.get_dataframe()

        t_values = t.ppf(1 - self.config.alpha / 2.0, predictions_df[dof_col])
        confidence_interval_radii = t_values * np.sqrt(predictions_df[predicted_value_var_col])

        if self.config.utility_function_name == "lower_confidence_bound_on_improvement":
            utility_function_values = predictions_df[predicted_value_col] * self._sign - confidence_interval_radii
        elif self.config.utility_function_name == "upper_confidence_bound_on_improvement":
            utility_function_values = predictions_df[predicted_value_col] * self._sign + confidence_interval_radii
        else:
            raise RuntimeError(f"Invalid utility function name: {self.config.utility_function_name}.")

        utility_function_values = pd.to_numeric(arg=utility_function_values, errors='raise')
        utility_df = pd.DataFrame(data=utility_function_values, index=predictions_df.index, columns=['utility'], dtype='float')
        assert utility_df.dtypes['utility'] == float, f"{utility_df} has the wrong type for the 'utility' column: {utility_df.dtypes['utility']}"
        return utility_df
