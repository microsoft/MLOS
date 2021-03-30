#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

import pytest
import math

import numpy as np
import pandas as pd

from mlos.Logger import create_logger

from mlos.OptimizerEvaluationTools.SyntheticFunctions.sample_functions import quadratic
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.Optimizers.BayesianOptimizerConfigStore import bayesian_optimizer_config_store

from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective

from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import Point, SimpleHypergrid, ContinuousDimension


class TestOptimizationProblem:
    """Basic tests for OptimizationProblem API.

    """
    def test_construct_feature_dataframe_context(self):
        def f(parameters, context):
            return pd.DataFrame({'function_value': -np.exp(-50 * (parameters.x - 0.5 * context.y -0.5) ** 2)})
        input_space = SimpleHypergrid(name="my_input_name", dimensions=[ContinuousDimension(name="x", min=0, max=1)])
        output_space = SimpleHypergrid(name="objective",
                                       dimensions=[ContinuousDimension(name="function_value", min=-10, max=10)])
        context_space = SimpleHypergrid(name="my_context_name", dimensions=[ContinuousDimension(name="y", min=-1, max=1)])

        optimization_problem = OptimizationProblem(
            parameter_space=input_space,
            objective_space=output_space,
            # we want to minimize the function
            objectives=[Objective(name="function_value", minimize=True)],
            context_space=context_space
        )
        n_samples = 100
        parameter_df = input_space.random_dataframe(n_samples)
        context_df = context_space.random_dataframe(n_samples)
        with pytest.raises(ValueError, match="Context required"):
            optimization_problem.construct_feature_dataframe(parameters_df=parameter_df)

        feature_df = optimization_problem.construct_feature_dataframe(
            parameters_df=parameter_df,
            context_df=context_df)

        assert isinstance(feature_df, pd.DataFrame)
        assert feature_df.shape == (n_samples, 3)
        assert (feature_df.columns == ['my_input_name.x', 'contains_context', 'my_context_name.y']).all()
        assert feature_df.contains_context.all()

    def test_construct_feature_dataframe_no_context(self):
        objective_function_config = objective_function_config_store.get_config_by_name('three_level_quadratic')
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )
        optimization_problem = OptimizationProblem(
            parameter_space=objective_function.parameter_space,
            objective_space=objective_function.output_space,
            objectives=[Objective(name='y', minimize=True)]
        )
        n_samples = 100
        parameter_df = optimization_problem.parameter_space.random_dataframe(n_samples)
        feature_df = optimization_problem.construct_feature_dataframe(parameters_df=parameter_df)
        assert feature_df.shape == (n_samples, len(optimization_problem.parameter_space.dimension_names) + 1)
        expected_columns = sorted([f"three_level_quadratic_config.{n}" for n in optimization_problem.parameter_space.dimension_names])
        assert (feature_df.columns[:-1].sort_values() == expected_columns).all()
        assert feature_df.columns[-1] == "contains_context"
        assert not feature_df.contains_context.any()
