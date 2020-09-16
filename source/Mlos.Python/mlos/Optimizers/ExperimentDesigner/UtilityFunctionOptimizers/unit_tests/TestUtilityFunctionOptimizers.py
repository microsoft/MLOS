#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import os
import unittest

import numpy as np
import pandas as pd

from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.RandomSearchOptimizer import RandomSearchOptimizer, RandomSearchOptimizerConfig
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.GlowWormSwarmOptimizer import GlowWormSwarmOptimizer, GlowWormSwarmOptimizerConfig
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.ConfidenceBoundUtilityFunction import ConfidenceBoundUtilityFunction
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel, HomogeneousRandomForestRegressionModelConfig
from mlos.Spaces import ContinuousDimension, SimpleHypergrid, Point
from mlos.SynthethicFunctions.HierarchicalFunctions import MultilevelQuadratic
from mlos.Tracer import Tracer

from mlos.SynthethicFunctions.sample_functions import quadratic
import mlos.global_values as global_values

class TestUtilityFunctionOptimizers(unittest.TestCase):
    """ Tests if the random search optimizer does anything useful at all.

    """

    @classmethod
    def setUpClass(cls):
        """ Set's up all the objects needed to test the RandomSearchOptimizer

        To test the RandomSearchOptimizer we need to first construct:
        * an optimization problem
        * a utility function

        To construct a utility function we need the same set up as in the TestConfidenceBoundUtilityFunction
        test.



        :return:
        """
        global_values.declare_singletons()
        global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)

        cls.input_space = SimpleHypergrid(
            name="input",
            dimensions=[
                ContinuousDimension(name='x_1', min=-0.5, max=0.5),
                ContinuousDimension(name='x_2', min=-0.5, max=0.5)
            ]
        )

        cls.output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        x_1, x_2 = np.meshgrid(
            cls.input_space['x_1'].linspace(num=51),
            cls.input_space['x_2'].linspace(num=51)
        )

        y = quadratic(x_1=x_1, x_2=x_2)


        cls.input_values_dataframe = pd.DataFrame({'x_1': x_1.reshape(-1), 'x_2': x_2.reshape(-1)})
        cls.output_values_dataframe = pd.DataFrame({'y': y.reshape(-1)})

        cls.model_config = HomogeneousRandomForestRegressionModelConfig()
        cls.model = HomogeneousRandomForestRegressionModel(
            model_config=cls.model_config,
            input_space=cls.input_space,
            output_space=cls.output_space
        )
        cls.model.fit(cls.input_values_dataframe, cls.output_values_dataframe, iteration_number=len(cls.input_values_dataframe.index))

        cls.utility_function_config = Point(
            utility_function_name="upper_confidence_bound_on_improvement",
            alpha=0.05
        )

        cls.optimization_problem = OptimizationProblem(
            parameter_space=cls.input_space,
            objective_space=cls.output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        cls.utility_function = ConfidenceBoundUtilityFunction(
            function_config=cls.utility_function_config,
            surrogate_model=cls.model,
            minimize=cls.optimization_problem.objectives[0].minimize
        )

    @classmethod
    def tearDownClass(cls) -> None:
        temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
        trace_output_path = os.path.join(temp_dir, "TestRandomSearchOptimizerTrace.json")
        print(f"Dumping trace to {trace_output_path}")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    def test_random_search_optimizer(self):
        print("##############################################")
        random_search_optimizer = RandomSearchOptimizer(
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            optimizer_config=RandomSearchOptimizerConfig.DEFAULT
        )
        for _ in range(5):
            suggested_params = random_search_optimizer.suggest()
            print(suggested_params)
            self.assertTrue(suggested_params in self.input_space)

    def test_glow_worm_swarm_optimizer(self):
        print("##############################################")
        glow_worm_swarm_optimizer = GlowWormSwarmOptimizer(
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            optimizer_config=GlowWormSwarmOptimizerConfig.DEFAULT
        )
        for _ in range(5):
            suggested_params = glow_worm_swarm_optimizer.suggest()
            print(suggested_params)
            self.assertTrue(suggested_params in self.input_space)

    def test_glow_worm_on_multilevel_quadratic(self):
        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        # Let's warm up the model a bit
        #
        num_warmup_samples = 1000
        random_params_df = MultilevelQuadratic.CONFIG_SPACE.random_dataframe(num_samples=num_warmup_samples)
        y = MultilevelQuadratic.evaluate_df(random_params_df)

        model = HomogeneousRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=MultilevelQuadratic.CONFIG_SPACE,
            output_space=output_space
        )
        model.fit(feature_values_pandas_frame=random_params_df, target_values_pandas_frame=y, iteration_number=num_warmup_samples)

        optimization_problem = OptimizationProblem(
            parameter_space=MultilevelQuadratic.CONFIG_SPACE,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        utility_function = ConfidenceBoundUtilityFunction(
            function_config=self.utility_function_config,
            surrogate_model=model,
            minimize=optimization_problem.objectives[0].minimize
        )

        glow_worm_swarm_optimizer = GlowWormSwarmOptimizer(
            optimization_problem=optimization_problem,
            utility_function=utility_function,
            optimizer_config=GlowWormSwarmOptimizerConfig.DEFAULT
        )

        num_iterations = 5
        for i in range(num_iterations):
            suggested_params = glow_worm_swarm_optimizer.suggest()
            print(f"[{i+1}/{num_iterations}] {suggested_params}")
            self.assertTrue(suggested_params in MultilevelQuadratic.CONFIG_SPACE)


