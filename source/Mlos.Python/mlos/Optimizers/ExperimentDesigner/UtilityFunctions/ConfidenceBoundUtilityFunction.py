#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

from mlos.Logger import create_logger
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, CategoricalDimension, Point
from mlos.Tracer import trace
from mlos.Optimizers.RegressionModels.Prediction import Prediction

class ConfidenceBoundUtilityFunctionConfig:
    CONFIG_SPACE = SimpleHypergrid(
        name="confidence_bound_utility_function_config",
        dimensions=[
            CategoricalDimension(name="utility_function_name", values=["lower_confidence_bound", "upper_confidence_bound"]),
            ContinuousDimension(name="num_standard_deviations", min=0, include_min=False, max=5)
        ]
    )
    DEFAULT = Point(
        utility_function_name="lower_confidence_bound",
        num_standard_deviations=3
    )

    @classmethod
    def create_from_config_point(cls, config_point):
        config_key_value_pairs = {param_name: value for param_name, value in config_point}
        return cls(**config_key_value_pairs)

    def __init__(
            self,
            utility_function_name=DEFAULT.utility_function_name,
            num_standard_deviations=DEFAULT.num_standard_deviations
    ):
        self.utility_function_name = utility_function_name
        self.num_standard_deviations = num_standard_deviations


class ConfidenceBoundUtilityFunction:
    def __init__(self, function_config: ConfidenceBoundUtilityFunctionConfig, surrogate_model, minimize, logger=None):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.config = function_config
        self.minimize = minimize
        self._sign = 1 if not minimize else -1
        if self.config.utility_function_name not in ("lower_confidence_bound", "upper_confidence_bound"):
            raise RuntimeError(f"Invalid utility function name: {self.config.utility_function_name}.")

        self.surrogate_model = surrogate_model

    @trace()
    def __call__(self, feature_values_pandas_frame):
        self.logger.debug(f"Computing utility values for {len(feature_values_pandas_frame.index)} points.")

        sample_mean_col = Prediction.LegalColumnNames.SAMPLE_MEAN.value
        sample_var_col = Prediction.LegalColumnNames.SAMPLE_VARIANCE.value

        predictions = self.surrogate_model.predict(feature_values_pandas_frame)
        predictions_df = predictions.get_dataframe()

        if self.config.utility_function_name == "lower_confidence_bound":
            utility_function_values = self._sign * (
                predictions_df[sample_mean_col] - self.config.num_standard_deviations * predictions_df[sample_var_col] ** 0.5)
        elif self.config.utility_function_name == "upper_confidence_bound":
            utility_function_values = self._sign * (
                predictions_df[sample_mean_col] + self.config.num_standard_deviations * predictions_df[sample_var_col] ** 0.5)
        else:
            raise RuntimeError(f"Invalid utility function name: {self.config.utility_function_name}.")

        return utility_function_values
