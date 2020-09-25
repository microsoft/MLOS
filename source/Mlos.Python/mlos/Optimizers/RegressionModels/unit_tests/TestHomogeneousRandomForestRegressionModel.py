#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import datetime
import math
import unittest
import numpy as np
import pandas as pd

from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel, homogeneous_random_forest_config_store
from mlos.Spaces import SimpleHypergrid, ContinuousDimension
import mlos.global_values as global_values


class TestHomogeneousRandomForestRegressionModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        global_values.declare_singletons()

    def setUp(self):
        # Let's create a simple linear mapping
        self.slope = 10
        self.y_intercept = 10
        self.input_values = np.linspace(start=0, stop=100, num=1000, endpoint=True)
        self.output_values = self.input_values * self.slope + self.y_intercept

        self.input_space = SimpleHypergrid(
            name="input",
            dimensions=[
                ContinuousDimension(name="x", min=0, max=100)
            ]
        )

        self.output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name="y", min=-math.inf, max=math.inf)
            ]
        )

        self.input_pandas_dataframe = pd.DataFrame({"x": self.input_values})
        self.output_pandas_dataframe = pd.DataFrame({"y": self.output_values})

    def test_default_homogeneous_random_forest_model(self):

        model_config = homogeneous_random_forest_config_store.default
        model = HomogeneousRandomForestRegressionModel(
            model_config=model_config,
            input_space=self.input_space,
            output_space=self.output_space
        )

        for i in range(2):
            model.fit(self.input_pandas_dataframe, self.output_pandas_dataframe, iteration_number=i)
            print("Random forest predictions")

            sample_inputs = {'x': np.linspace(start=-10, stop=110, num=13, endpoint=True)}
            sample_inputs_pandas_dataframe = pd.DataFrame(sample_inputs)
            predictions = model.predict(sample_inputs_pandas_dataframe)
            for sample_input, prediction in zip(sample_inputs_pandas_dataframe['x'],
                                                predictions.get_dataframe().iterrows()):
                print(sample_input, prediction)


    def test_random_random_forest_models(self):
        """ Test's random forests with random configs

        :return:
        """
        sample_inputs = {'x': np.linspace(start=-10, stop=110, num=121, endpoint=True)}
        sample_inputs_pandas_dataframe = pd.DataFrame(sample_inputs)

        num_iterations = 5
        for i in range(num_iterations):
            if i % 10 == 0:
                print(f"{datetime.datetime.utcnow()} {i}/{num_iterations}")

            model_config = homogeneous_random_forest_config_store.parameter_space.random()
            model_config.n_estimators = min(model_config.n_estimators, 20)
            print(model_config)
            model = HomogeneousRandomForestRegressionModel(
                model_config=model_config,
                input_space=self.input_space,
                output_space=self.output_space
            )
            model.fit(self.input_pandas_dataframe, self.output_pandas_dataframe, iteration_number=i)
            predictions = model.predict(sample_inputs_pandas_dataframe)
            for sample_input, prediction in zip(sample_inputs_pandas_dataframe['x'], predictions.get_dataframe().iterrows()):
                print(sample_input, prediction)
