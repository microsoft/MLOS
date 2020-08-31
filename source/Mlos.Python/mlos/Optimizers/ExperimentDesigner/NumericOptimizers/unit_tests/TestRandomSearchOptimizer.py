#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import unittest

import numpy as np
import pandas as pd

from mlos.Optimizers.ExperimentDesigner.NumericOptimizers.RandomSearchOptimizer import RandomSearchOptimizer, RandomSearchOptimizerConfig
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.ConfidenceBoundUtilityFunction import ConfidenceBoundUtilityFunction, ConfidenceBoundUtilityFunctionConfig
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel, HomogeneousRandomForestRegressionModelConfig
from mlos.Spaces import SimpleHypergrid, ContinuousDimension

from mlos.SynthethicFunctions.sample_functions import quadratic
import mlos.global_values as global_values

class TestRandomSearchOptimizer(unittest.TestCase):
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

        cls.input_space = SimpleHypergrid(
            name="input",
            dimensions=[
                ContinuousDimension(name='x_1', min=-100, max=100),
                ContinuousDimension(name='x_2', min=-100, max=100)
            ]
        )

        cls.output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        x_1, x_2 = np.meshgrid(
            cls.input_space['x_1'].linspace(num=201),
            cls.input_space['x_2'].linspace(num=201)
        )

        y = -quadratic(x_1=x_1, x_2=x_2)


        cls.input_values_dataframe = pd.DataFrame({'x_1': x_1.reshape(-1), 'x_2': x_2.reshape(-1)})
        cls.output_values_dataframe = pd.DataFrame({'y': y.reshape(-1)})

        cls.model_config = HomogeneousRandomForestRegressionModelConfig()
        cls.model = HomogeneousRandomForestRegressionModel(
            model_config=cls.model_config,
            input_space=cls.input_space,
            output_space=cls.output_space
        )
        cls.model.fit(cls.input_values_dataframe, cls.output_values_dataframe)

        cls.utility_function_config = ConfidenceBoundUtilityFunctionConfig(
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


    def test_random_search_optimizer(self):

        random_search_optimizer = RandomSearchOptimizer(
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            optimizer_config=RandomSearchOptimizerConfig()
        )
        for _ in range(100):
            suggested_params = random_search_optimizer.suggest()
            self.assertTrue(suggested_params in self.input_space)
