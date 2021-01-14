#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import os

import numpy as np
import pandas as pd

from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.RandomSearchOptimizer import RandomSearchOptimizer, random_search_optimizer_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.GlowWormSwarmOptimizer import GlowWormSwarmOptimizer, glow_worm_swarm_optimizer_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.ConfidenceBoundUtilityFunction import ConfidenceBoundUtilityFunction
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestConfigStore import homogeneous_random_forest_config_store
from mlos.Optimizers.RegressionModels.MultiObjectiveHomogeneousRandomForest import MultiObjectiveHomogeneousRandomForest
from mlos.Spaces import ContinuousDimension, SimpleHypergrid, Point
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.Tracer import Tracer, trace
import mlos.global_values as global_values

class TestUtilityFunctionOptimizers:
    """ Tests if the random search optimizer does anything useful at all.

    """

    @classmethod
    def setup_class(cls):
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

        objective_function_config = objective_function_config_store.get_config_by_name('2d_quadratic_concave_up')
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)

        cls.input_space = objective_function.parameter_space
        cls.output_space = objective_function.output_space

        cls.input_values_dataframe = objective_function.parameter_space.random_dataframe(num_samples=2500)
        cls.output_values_dataframe = objective_function.evaluate_dataframe(cls.input_values_dataframe)

        cls.model_config = homogeneous_random_forest_config_store.default

        print(cls.model_config)

        cls.model = MultiObjectiveHomogeneousRandomForest(
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
    def teardown_class(cls) -> None:
        temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
        trace_output_path = os.path.join(temp_dir, "TestUtilityFunctionOptimizers.json")
        print(f"Dumping trace to {trace_output_path}")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    @trace()
    def test_random_search_optimizer(self):
        print("##############################################")
        random_search_optimizer = RandomSearchOptimizer(
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            optimizer_config=random_search_optimizer_config_store.default
        )
        for _ in range(5):
            suggested_params = random_search_optimizer.suggest()
            print(suggested_params.to_json())
            assert suggested_params in self.input_space

    @trace()
    def test_glow_worm_swarm_optimizer(self):
        print("##############################################")
        glow_worm_swarm_optimizer = GlowWormSwarmOptimizer(
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            optimizer_config=glow_worm_swarm_optimizer_config_store.default
        )
        for _ in range(5):
            suggested_params = glow_worm_swarm_optimizer.suggest()
            print(suggested_params.to_json())
            assert suggested_params in self.input_space

    @trace()
    def test_glow_worm_on_three_level_quadratic(self):
        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        objective_function_config = objective_function_config_store.get_config_by_name('three_level_quadratic')
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)
        # Let's warm up the model a bit
        #
        num_warmup_samples = 1000
        random_params_df = objective_function.parameter_space.random_dataframe(num_samples=num_warmup_samples)
        y = objective_function.evaluate_dataframe(random_params_df)

        model = MultiObjectiveHomogeneousRandomForest(
            model_config=self.model_config,
            input_space=objective_function.parameter_space,
            output_space=output_space
        )
        model.fit(features_df=random_params_df, targets_df=y, iteration_number=num_warmup_samples)

        optimization_problem = OptimizationProblem(
            parameter_space=objective_function.parameter_space,
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
            optimizer_config=glow_worm_swarm_optimizer_config_store.default
        )

        num_iterations = 5
        for i in range(num_iterations):
            suggested_params = glow_worm_swarm_optimizer.suggest()
            print(f"[{i+1}/{num_iterations}] {suggested_params.to_json()}")
            assert suggested_params in objective_function.parameter_space


