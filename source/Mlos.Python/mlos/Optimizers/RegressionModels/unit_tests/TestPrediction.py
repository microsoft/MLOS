#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import unittest
import numpy as np
import pandas as pd

from mlos.Optimizers.RegressionModels.Prediction import Prediction

import mlos.global_values as global_values
global_values.declare_singletons()

class TestPrediction(unittest.TestCase):

    class MockValidRegressionModelPrediction(Prediction):
        all_prediction_fields = Prediction.LegalColumnNames
        OUTPUTS = [
            all_prediction_fields.SAMPLE_MEAN,
            all_prediction_fields.SAMPLE_VARIANCE,
            all_prediction_fields.SAMPLE_SIZE]

        def __init__(self, objective_name: str):
            super().__init__(objective_name=objective_name, predictor_outputs=TestPrediction.MockValidRegressionModelPrediction.OUTPUTS)

    @classmethod
    def classSetUp(cls):
        global_values.declare_singletons()

    def setUp(self):
        # Create a mock regression model prediction class
        self.test_regression_prediction = TestPrediction.MockValidRegressionModelPrediction(objective_name='y_test')

    def test_creating_invalid_output_types(self):
        # try creating a PREDICTION_SCHEMA with values outside the Prediction.PredictionSchema enum
        class MockInvalidRegressionModelPrediction1(Prediction):
            OUTPUTS = ['SAMPLE_MEAN_foo', 'SAMPLE_VARIANCE', 'SAMPLE_SIZE']

            def __init__(self, objective_name: str):
                super().__init__(objective_name=objective_name, predictor_outputs=MockInvalidRegressionModelPrediction1.OUTPUTS)

        with self.assertRaises(AssertionError):
            MockInvalidRegressionModelPrediction1(objective_name='test2')

    def test_set_dataframe_with_extra_columns(self):
        # passing back a dataframe with columns not included in the model's PREDICTION_SCHEMA
        num_predictions = 10
        example_df = pd.DataFrame({
            'y_1': np.random.uniform(0, 1, size=num_predictions),
            'sample_mean': np.random.normal(0, 1, size=num_predictions),
            'sample_variance': np.random.chisquare(5, size=num_predictions),
            'sample_size': np.random.poisson(20, size=num_predictions)
        })
        with self.assertRaises(AssertionError):
            self.test_regression_prediction.set_dataframe(example_df)

    def test_set_dataframe_with_missing_columns(self):
        # fail to pass back an expected column defined in the model's PREDICTION_SCHEMA
        num_predictions = 10
        example_df = pd.DataFrame({
            'sample_variance': np.random.chisquare(5, size=num_predictions),
            'sample_size': np.random.poisson(20, size=num_predictions)
        })
        with self.assertRaises(AssertionError):
            self.test_regression_prediction.set_dataframe(example_df)
