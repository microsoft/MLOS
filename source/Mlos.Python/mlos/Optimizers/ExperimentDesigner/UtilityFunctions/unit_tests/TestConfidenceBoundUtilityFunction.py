#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import unittest

import numpy as np
import pandas as pd

from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import \
    HomogeneousRandomForestRegressionModel, HomogeneousRandomForestRegressionModelConfig
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.ConfidenceBoundUtilityFunction import \
    ConfidenceBoundUtilityFunction, ConfidenceBoundUtilityFunctionConfig

from mlos.Spaces import SimpleHypergrid, ContinuousDimension
import mlos.global_values as global_values



class TestConfidenceBoundUtilityFunction(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        global_values.declare_singletons()

        cls.slope = 10
        cls.y_intercept = 10
        cls.input_values = np.linspace(start=0, stop=100, num=1000, endpoint=True)
        cls.output_values = cls.input_values * cls.slope + cls.y_intercept

        cls.input_space = SimpleHypergrid(
            name="input",
            dimensions=[ContinuousDimension(name="x", min=0, max=100)]
        )

        cls.output_space = SimpleHypergrid(
            name="output",
            dimensions=[ContinuousDimension(name="y", min=-math.inf, max=math.inf)]
        )

        cls.input_pandas_dataframe = pd.DataFrame({"x": cls.input_values})
        cls.output_pandas_dataframe = pd.DataFrame({"y": cls.output_values})

        cls.model_config = HomogeneousRandomForestRegressionModelConfig()
        cls.model = HomogeneousRandomForestRegressionModel(
            model_config=cls.model_config,
            input_space=cls.input_space,
            output_space=cls.output_space
        )
        cls.model.fit(cls.input_pandas_dataframe, cls.output_pandas_dataframe)

        cls.sample_inputs = {'x': np.linspace(start=-10, stop=110, num=13, endpoint=True)}
        cls.sample_inputs_pandas_dataframe = pd.DataFrame(cls.sample_inputs)
        cls.sample_predictions = cls.model.predict(cls.sample_inputs_pandas_dataframe)


    def test_lower_confidence_bound(self):
        """Tests if the lower confidence bound utility function is behaving properly."""
        utility_function_config = ConfidenceBoundUtilityFunctionConfig(
            utility_function_name="lower_confidence_bound",
            num_standard_deviations=3
        )

        utility_function = ConfidenceBoundUtilityFunction(
            function_config=utility_function_config,
            surrogate_model=self.model,
            minimize=False
        )

        sample_mean_col = Prediction.LegalColumnNames.SAMPLE_MEAN.value
        sample_var_col = Prediction.LegalColumnNames.SAMPLE_VARIANCE.value

        prediction_df = self.sample_predictions.get_dataframe()
        expected_utility_function_values = prediction_df[sample_mean_col] - 3 * prediction_df[sample_var_col].apply('sqrt')
        utility_function_values = utility_function(self.sample_inputs_pandas_dataframe)
        for expected, actual in zip(expected_utility_function_values, utility_function_values):
            self.assertTrue((expected == actual) or (np.isnan(expected) and np.isnan(actual)))

    def test_random_function_configs(self):
        for _ in range(100):
            utility_function_config_point = ConfidenceBoundUtilityFunctionConfig.CONFIG_SPACE.random()
            utility_function_config = ConfidenceBoundUtilityFunctionConfig.create_from_config_point(
                utility_function_config_point)
            utility_function = ConfidenceBoundUtilityFunction(
                function_config=utility_function_config,
                surrogate_model=self.model,
                minimize=False
            )

            sample_mean_col = Prediction.LegalColumnNames.SAMPLE_MEAN.value
            sample_var_col = Prediction.LegalColumnNames.SAMPLE_VARIANCE.value

            sign = -1 if utility_function_config.utility_function_name == 'lower_confidence_bound' else 1
            prediction_df = self.sample_predictions.get_dataframe()
            expected_utility_function_values = prediction_df[sample_mean_col] + \
                                               sign * utility_function_config.num_standard_deviations * prediction_df[sample_var_col].apply('sqrt')
            utility_function_values = utility_function(self.sample_inputs_pandas_dataframe)

            for expected, actual in zip(expected_utility_function_values, utility_function_values):
                self.assertTrue((expected == actual) or (np.isnan(expected) and np.isnan(actual)))
