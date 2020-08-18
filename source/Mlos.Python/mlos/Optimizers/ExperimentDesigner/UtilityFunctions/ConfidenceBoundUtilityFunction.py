#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math

from mlos.Logger import create_logger
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, CategoricalDimension, Point
from mlos.Tracer import trace

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
        if self.config.utility_function_name == "lower_confidence_bound":
            self._utility_function_implementation = self.lower_confidence_bound
        elif self.config.utility_function_name == "upper_confidence_bound":
            self._utility_function_implementation = self.upper_confidence_bound
        else:
            raise RuntimeError(f"Invalid utility function name: {self.config.utility_function_name}.")

        self.surrogate_model = surrogate_model

    @trace()
    def __call__(self, feature_values_pandas_frame):
        self.logger.debug(f"Computing utility values for {len(feature_values_pandas_frame.index)} points.")
        predictions = self.surrogate_model.predict(feature_values_pandas_frame)

        # If no prediction was possible, we return the value of utility function to be -infinity
        # TODO: this might not be desirable - consider alternative approaches.
        utility_function_values = [
            self._sign * self._utility_function_implementation(prediction)
            if prediction is not None else -math.inf
            for prediction in predictions
        ]
        return utility_function_values

    def lower_confidence_bound(self, prediction):
        return prediction.mean - prediction.standard_deviation * self.config.num_standard_deviations

    def upper_confidence_bound(self, prediction):
        return prediction.mean + prediction.standard_deviation * self.config.num_standard_deviations
