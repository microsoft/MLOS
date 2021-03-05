#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import pytest

import numpy as np
import pandas as pd

from mlos.OptimizerEvaluationTools.SyntheticFunctions.EnvelopedWaves import EnvelopedWaves, enveloped_waves_config_space
from mlos.OptimizerEvaluationTools.SyntheticFunctions.MultiObjectiveEnvelopedWaves import \
    MultiObjectiveEnvelopedWaves, \
    multi_objective_enveloped_waves_config_space, \
    multi_objective_enveloped_waves_config_store
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Spaces import Point


class TestEnvelopedWaves:

    def test_enveloped_waves(self):
        vertical_shift = 1
        for num_params in range(1, 10):
            function_config = Point(
                num_params=num_params,
                num_periods=1,
                amplitude=1,
                vertical_shift=vertical_shift,
                phase_shift=0,
                period=2 * math.pi,
                envelope_type="none"
            )

            assert function_config in enveloped_waves_config_space
            objective_function = EnvelopedWaves(function_config)
            random_params_df = objective_function.parameter_space.random_dataframe(100)
            objectives_df = objective_function.evaluate_dataframe(random_params_df)
            assert ((objectives_df['y'] <= (num_params + vertical_shift)) & (objectives_df['y'] >= -num_params + vertical_shift)).all()

    def test_random_configs(self):
        for _ in range(100):
            function_config = enveloped_waves_config_space.random()
            objective_function = EnvelopedWaves(function_config)
            random_params_df = objective_function.parameter_space.random_dataframe(100)
            objectives_df = objective_function.evaluate_dataframe(random_params_df)
            assert objective_function.output_space.get_valid_rows_index(objectives_df).equals(objectives_df.index)

    @pytest.mark.parametrize('i', [i for i in range(100)])
    def test_random_multi_objective_configs(self, i):
        function_config = multi_objective_enveloped_waves_config_space.random()
        print(f"[{i}] Function config: {function_config}")
        objective_function = MultiObjectiveEnvelopedWaves(function_config)
        random_params_df = objective_function.parameter_space.random_dataframe(100)
        objectives_df = objective_function.evaluate_dataframe(random_params_df)
        assert objective_function.output_space.get_valid_rows_index(objectives_df).equals(objectives_df.index)


    @pytest.mark.parametrize('function_config_name', ["pi_phase_difference", "no_phase_difference", "half_pi_phase_difference"])
    def test_pareto_shape(self, function_config_name):
        """Tests if the pareto frontier has the expected shape.

        For no phase difference, we would expect a pareto frontier to be a single point.
        For a phase difference of pi / 2 we would expect the pareto frontier to be on a quarter circle.
        For a phase difference of pi we would expect the pareto frontier to be on a diagonal.
        """

        function_config = multi_objective_enveloped_waves_config_store.get_config_by_name(function_config_name)
        objective_function = MultiObjectiveEnvelopedWaves(function_config)

        optimization_problem = OptimizationProblem(
            parameter_space=objective_function.parameter_space,
            objective_space=objective_function.output_space,
            objectives=[Objective(name=dim_name, minimize=False) for dim_name in objective_function.output_space.dimension_names]
        )

        # Let's create a meshgrid of all params.
        # TODO: add this as a function in Hypergrids

        num_points = 100 if function_config_name != "pi_phase_difference" else 10
        linspaces = [dimension.linspace(num_points) for dimension in objective_function.parameter_space.dimensions]
        meshgrids = np.meshgrid(*linspaces)
        flat_meshgrids = [meshgrid.flatten() for meshgrid in meshgrids]
        params_df = pd.DataFrame({
            dim_name: flat_meshgrid
            for dim_name, flat_meshgrid
            in zip(objective_function.parameter_space.dimension_names, flat_meshgrids)
        })
        objectives_df = objective_function.evaluate_dataframe(params_df)
        pareto_frontier = ParetoFrontier(optimization_problem=optimization_problem, objectives_df=objectives_df, parameters_df=params_df)
        pareto_df = pareto_frontier.pareto_df

        if function_config_name == "no_phase_difference":
            # Let's assert that the optimum is close to 4 and that all selected params are close to half of pi.
            assert len(pareto_df.index) == 1
            for objective in optimization_problem.objectives:
                assert abs(pareto_df[objective.name].iloc[0] - 3) < 0.001

            optimal_params_df = params_df.iloc[pareto_df.index]
            for param_name in objective_function.parameter_space.dimension_names:
                assert abs(optimal_params_df[param_name].iloc[0] - math.pi / 2) < 0.02

        if function_config_name == "half_pi_phase_difference":
            expected_radius = 3
            pareto_df['radius'] = np.sqrt(pareto_df['y0'] ** 2 + pareto_df['y1'] ** 2)
            pareto_df['error'] = pareto_df['radius'] - expected_radius
            assert (np.abs(pareto_df['error']) < 0.01).all()

        if function_config_name == "pi_phase_difference":
            # We expect that the absolute values of our objectives will be nearly identical.
            #
            assert (np.abs(pareto_df['y0'] + pareto_df['y1']) < 0.01).all()
