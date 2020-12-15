#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Tracer import trace
from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from .UtilityFunction import UtilityFunction


class PredictedValueUtilityFunction(UtilityFunction):
    def __init__(self, surrogate_model, minimize, logger=None):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.minimize = minimize
        self._sign = 1 if not minimize else -1
        self.surrogate_model = surrogate_model

    @trace()
    def __call__(self, feature_values_pandas_frame):
        self.logger.debug(f"Computing utility values for {len(feature_values_pandas_frame.index)} points.")

        predictions = self.surrogate_model.predict(features_df=feature_values_pandas_frame)[0]
        predictions_df = predictions.get_dataframe()
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value

        return self._sign * predictions_df[[predicted_value_col]].rename(columns={predicted_value_col: 'utility'})
