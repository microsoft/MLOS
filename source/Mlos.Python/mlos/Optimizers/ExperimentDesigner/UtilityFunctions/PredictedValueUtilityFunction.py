#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Tracer import trace
from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from .UtilityFunction import UtilityFunction


class PredictedValueUtilityFunction(UtilityFunction):
    def __init__(
        self,
        surrogate_model: MultiObjectiveRegressionModel,
        minimize: bool,
        logger=None
    ):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.minimize = minimize
        self._sign = 1 if not minimize else -1
        self.surrogate_model = surrogate_model

    @trace()
    def __call__(self, feature_values_pandas_frame):
        self.logger.debug(f"Computing utility values for {len(feature_values_pandas_frame.index)} points.")

        multi_objective_predictions = self.surrogate_model.predict(features_df=feature_values_pandas_frame)

        # While the models can predict multiple objectives, here we just compute the utility for the first one. Next-steps include:
        #   1. Select the objective by name
        #   2. Write multi-objective utility functions
        #
        # But for now, the behavior below keeps the behavior of the optimizer unchanged.
        #
        predictions = multi_objective_predictions[0]
        predictions_df = predictions.get_dataframe()
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value

        return self._sign * predictions_df[[predicted_value_col]].rename(columns={predicted_value_col: 'utility'})
