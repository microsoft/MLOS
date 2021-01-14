#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
from scipy.stats import t

import numpy as np
import pandas as pd

from mlos.Optimizers.RegressionModels.MultiObjectiveHomogeneousRandomForest import MultiObjectiveHomogeneousRandomForest
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestConfigStore import homogeneous_random_forest_config_store
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.ConfidenceBoundUtilityFunction import \
    ConfidenceBoundUtilityFunction, confidence_bound_utility_function_config_store

from mlos.Spaces import ContinuousDimension, Point, SimpleHypergrid
import mlos.global_values as global_values



class TestConfidenceBoundUtilityFunction:

    @classmethod
    def setup_class(cls) -> None:
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

        cls.model_config = homogeneous_random_forest_config_store.default
        cls.model = MultiObjectiveHomogeneousRandomForest(
            model_config=cls.model_config,
            input_space=cls.input_space,
            output_space=cls.output_space
        )
        cls.model.fit(cls.input_pandas_dataframe, cls.output_pandas_dataframe, iteration_number=len(cls.input_pandas_dataframe.index))

        cls.sample_inputs = {'x': np.linspace(start=-10, stop=110, num=13, endpoint=True)}
        cls.sample_inputs_pandas_dataframe = pd.DataFrame(cls.sample_inputs)
        cls.sample_predictions = cls.model.predict(cls.sample_inputs_pandas_dataframe)[0]


    def test_lower_confidence_bound(self):
        """Tests if the lower confidence bound utility function is behaving properly."""
        utility_function_config = Point(
            utility_function_name="lower_confidence_bound_on_improvement",
            alpha=0.01
        )

        utility_function = ConfidenceBoundUtilityFunction(
            function_config=utility_function_config,
            surrogate_model=self.model,
            minimize=False
        )

        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        prediction_df = self.sample_predictions.get_dataframe()

        t_values = t.ppf(1 - utility_function_config.alpha / 2.0, prediction_df[dof_col])
        confidence_interval_radii = t_values * prediction_df[predicted_value_var_col].apply('sqrt')

        expected_utility_function_values = prediction_df[predicted_value_col] - confidence_interval_radii
        utility_function_values = utility_function(self.sample_inputs_pandas_dataframe)['utility']
        for expected, actual in zip(expected_utility_function_values, utility_function_values):
            assert (expected == actual) or (np.isnan(expected) and np.isnan(actual))

    def test_random_function_configs(self):
        for i in range(100):
            minimize = [True, False][i % 2]
            utility_function_config = confidence_bound_utility_function_config_store.parameter_space.random()
            utility_function = ConfidenceBoundUtilityFunction(
                function_config=utility_function_config,
                surrogate_model=self.model,
                minimize=minimize
            )

            predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
            predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
            dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

            sign = -1 if minimize else 1
            prediction_df = self.sample_predictions.get_dataframe()
            t_values = t.ppf(1 - utility_function_config.alpha / 2.0, prediction_df[dof_col])
            confidence_interval_radii = t_values * prediction_df[predicted_value_var_col].apply('sqrt')
            if utility_function_config.utility_function_name == 'lower_confidence_bound_on_improvement':
                expected_utility_function_values = sign * prediction_df[predicted_value_col] - confidence_interval_radii
            else:
                expected_utility_function_values = sign * prediction_df[predicted_value_col] + confidence_interval_radii
            utility_function_values = utility_function(self.sample_inputs_pandas_dataframe)['utility']

            for expected, actual in zip(expected_utility_function_values, utility_function_values):
                assert (expected == actual) or (np.isnan(expected) and np.isnan(actual))
