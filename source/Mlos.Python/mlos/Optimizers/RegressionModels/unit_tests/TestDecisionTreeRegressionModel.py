#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import datetime
import math
import os
import unittest

import numpy as np
import pandas as pd

import mlos.global_values as global_values
from mlos.Optimizers.RegressionModels.DecisionTreeRegressionModel import DecisionTreeRegressionModel, decision_tree_config_store
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Spaces import SimpleHypergrid, ContinuousDimension
from mlos.Tracer import Tracer

class TestDecisionTreeRegressionModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        global_values.declare_singletons()
        global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)

    @classmethod
    def tearDownClass(cls) -> None:
        temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
        trace_output_path = os.path.join(temp_dir, "TestDecisionTreeRegressionModel.json")
        print(f"Dumping trace to {trace_output_path}")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    def setUp(self):
        # Let's create a simple linear mapping
        self.slope = 10
        self.y_intercept = 10
        self.input_values = np.linspace(start=0, stop=100, num=101, endpoint=True)
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

    def test_default_decision_tree_model(self):
        model_config = decision_tree_config_store.default
        model = DecisionTreeRegressionModel(
            model_config=model_config,
            input_space=self.input_space,
            output_space=self.output_space
        )
        model.fit(self.input_pandas_dataframe, self.output_pandas_dataframe, iteration_number=len(self.input_pandas_dataframe.index))
        gof_metrics = model.compute_goodness_of_fit(features_df=self.input_pandas_dataframe, target_df=self.output_pandas_dataframe, data_set_type=DataSetType.TRAIN)
        print(gof_metrics)


    def test_random_decision_tree_models(self):
        sample_inputs_pandas_dataframe = self.input_space.random_dataframe(num_samples=100)

        num_iterations = 50
        for i in range(num_iterations):
            if i % 10 == 0:
                print(f"{datetime.datetime.utcnow()} {i}/{num_iterations}")
            model_config = decision_tree_config_store.parameter_space.random()
            print(str(model_config))
            model = DecisionTreeRegressionModel(
                model_config=model_config,
                input_space=self.input_space,
                output_space=self.output_space
            )
            model.fit(self.input_pandas_dataframe, self.output_pandas_dataframe, iteration_number=len(sample_inputs_pandas_dataframe.index))
            gof_metrics = model.compute_goodness_of_fit(features_df=self.input_pandas_dataframe, target_df=self.output_pandas_dataframe, data_set_type=DataSetType.TRAIN)
            print(gof_metrics)

