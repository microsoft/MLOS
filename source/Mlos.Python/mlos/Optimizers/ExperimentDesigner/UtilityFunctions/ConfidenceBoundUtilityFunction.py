#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from scipy.stats import t
from mlos.Logger import create_logger
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, CategoricalDimension, Point, DefaultConfigMeta
from mlos.Tracer import trace
from mlos.Optimizers.RegressionModels.Prediction import Prediction

class ConfidenceBoundUtilityFunctionConfig(metaclass=DefaultConfigMeta):
    CONFIG_SPACE = SimpleHypergrid(
        name="confidence_bound_utility_function_config",
        dimensions=[
            CategoricalDimension(name="utility_function_name", values=["lower_confidence_bound_on_improvement", "upper_confidence_bound_on_improvement"]),
            ContinuousDimension(name="alpha", min=0.01, max=0.2)
        ]
    )
    _DEFAULT = Point(
        utility_function_name="upper_confidence_bound_on_improvement",
        alpha=0.01
    )

    @classmethod
    def create_from_config_point(cls, config_point):
        config_key_value_pairs = {param_name: value for param_name, value in config_point}
        return cls(**config_key_value_pairs)

    def __init__(
            self,
            utility_function_name=_DEFAULT.utility_function_name,
            alpha=_DEFAULT.alpha
    ):
        self.utility_function_name = utility_function_name
        self.alpha = alpha


class ConfidenceBoundUtilityFunction:
    def __init__(self, function_config: ConfidenceBoundUtilityFunctionConfig, surrogate_model, minimize, logger=None):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.config = function_config
        self.minimize = minimize
        self._sign = 1 if not minimize else -1
        if self.config.utility_function_name not in ("lower_confidence_bound_on_improvement", "upper_confidence_bound_on_improvement"):
            raise RuntimeError(f"Invalid utility function name: {self.config.utility_function_name}.")

        self.surrogate_model = surrogate_model

    @trace()
    def __call__(self, feature_values_pandas_frame):
        self.logger.debug(f"Computing utility values for {len(feature_values_pandas_frame.index)} points.")

        sample_mean_col = Prediction.LegalColumnNames.SAMPLE_MEAN.value
        mean_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        dof_col = Prediction.LegalColumnNames.DEGREES_OF_FREEDOM.value

        predictions = self.surrogate_model.predict(feature_values_pandas_frame)
        predictions_df = predictions.get_dataframe()

        t_values = t.ppf(1 - self.config.alpha / 2.0, predictions_df[dof_col])
        confidence_interval_radii = t_values * predictions_df[mean_var_col].apply('sqrt')

        if self.config.utility_function_name == "lower_confidence_bound_on_improvement":
            utility_function_values = predictions_df[sample_mean_col] * self._sign - confidence_interval_radii
        elif self.config.utility_function_name == "upper_confidence_bound_on_improvement":
            utility_function_values = predictions_df[sample_mean_col] * self._sign + confidence_interval_radii
        else:
            raise RuntimeError(f"Invalid utility function name: {self.config.utility_function_name}.")

        return utility_function_values
