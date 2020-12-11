#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import pytest
from typing import List

import numpy as np
import pandas as pd

from mlos.OptimizerEvaluationTools.SyntheticFunctions.Hypersphere import Hypersphere
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid


class TestParetoFrontier:
    """Tests if the ParetoFrontier works."""

    def test_basic_functionality_on_2d_objective_space(self):
        """Basic sanity check. Mainly used to help us develop the API.
        """

        # Let's just create a bunch of random points, build a pareto frontier
        # and verify that the invariants hold.
        #
        parameter_space = SimpleHypergrid(
            name='params',
            dimensions=[
                ContinuousDimension(name='x1', min=0, max=10)
            ]
        )

        objective_space = SimpleHypergrid(
            name='objectives',
            dimensions=[
                ContinuousDimension(name='y1', min=0, max=10),
                ContinuousDimension(name='y2', min=0, max=10)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=parameter_space,
            objective_space=objective_space,
            objectives=[
                Objective(name='y1', minimize=False),
                Objective(name='y2', minimize=False)
            ]
        )

        num_rows = 100000
        random_params_df = parameter_space.random_dataframe(num_rows)
        random_objectives_df = objective_space.random_dataframe(num_rows)

        pareto_df = ParetoFrontier.compute_pareto(
            optimization_problem=optimization_problem,
            objectives_df=random_objectives_df
        )

        non_pareto_index = random_objectives_df.index.difference(pareto_df.index)
        for i, row in pareto_df.iterrows():
            # Now let's make sure that no point in pareto is dominated by any non-pareto point.
            #
            assert (random_objectives_df.loc[non_pareto_index] < row).any(axis=1).sum() == len(non_pareto_index)

            # Let's also make sure that no point on the pareto is dominated by any other point there.
            #
            other_rows = pareto_df.index.difference([i])
            assert (pareto_df.loc[other_rows] > row).all(axis=1).sum() == 0


    @pytest.mark.parametrize("minimize", ["all", "none", "some"])
    @pytest.mark.parametrize("num_output_dimensions", [2, 10])
    @pytest.mark.parametrize("num_points", [100, 1000])
    def test_hyperspheres(self, minimize, num_output_dimensions, num_points):
        """Uses a hypersphere to validate that ParetoFrontier can correctly identify pareto-optimal points."""


        hypersphere_radius = 10

        objective_function_config = Point(
            implementation=Hypersphere.__name__,
            hypersphere_config=Point(
                num_objectives=num_output_dimensions,
                minimize=minimize,
                radius=hypersphere_radius
            )
        )

        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)
        optimization_problem = objective_function.default_optimization_problem
        random_params_df = optimization_problem.parameter_space.random_dataframe(num_points)

        # Let's randomly subsample 10% of points in random_params_df and make those points pareto optimal.
        #
        optimal_points_index = random_params_df.sample(
            frac=0.1,
            replace=False,
            axis='index'
        ).index

        random_params_df.loc[optimal_points_index, ['radius']] = hypersphere_radius
        objectives_df = objective_function.evaluate_dataframe(dataframe=random_params_df)



        # Conveniently, we can double check all of our math by invoking Pythagoras. Basically:
        #
        #   assert y0**2 + y1**2 + ... == radius**2
        #
        assert (np.power(objectives_df, 2).sum(axis=1) - np.power(random_params_df["radius"], 2) < 0.000001).all()


        # Just a few more sanity checks before we do the pareto computation.
        #
        if minimize == "all":
            assert (objectives_df <= 0).all().all()
        elif minimize == "none":
            assert (objectives_df >= 0).all().all()
        else:
            for column, minimize_column in zip(objectives_df, objective_function.minimize_mask):
                if minimize_column:
                    assert (objectives_df[column] <= 0).all()
                else:
                    assert (objectives_df[column] >= 0).all()


        pareto_df = ParetoFrontier.compute_pareto(
            optimization_problem=optimization_problem,
            objectives_df=objectives_df
        )

        # We know that all of the pareto efficient points must be on the frontier.
        #
        assert optimal_points_index.difference(pareto_df.index.intersection(optimal_points_index)).empty
        assert len(pareto_df.index) >= len(optimal_points_index)

        # If we flip all minimized objectives, we can assert on even more things.
        #
        for column, minimize_column in zip(objectives_df, objective_function.minimize_mask):
            if minimize_column:
                objectives_df[column] = -objectives_df[column]
                pareto_df[column] = - pareto_df[column]

        non_pareto_index = objectives_df.index.difference(pareto_df.index)
        for i, row in pareto_df.iterrows():
            # Now let's make sure that no point in pareto is dominated by any non-pareto point.
            #
            assert (objectives_df.loc[non_pareto_index] < row).any(axis=1).sum() == len(non_pareto_index)

            # Let's also make sure that no point on the pareto is dominated by any other point there.
            #
            other_rows = pareto_df.index.difference([i])
            assert (pareto_df.loc[other_rows] > row).all(axis=1).sum() == 0


    def test_repeated_values(self):
        """Validates that the algorithm does its job in the presence of repeated values.

        :return:
        """

        optimization_problem = OptimizationProblem(
            parameter_space=None,
            objective_space=SimpleHypergrid(
                name="objectives",
                dimensions=[
                    ContinuousDimension(name='y1', min=0, max=5),
                    ContinuousDimension(name='y2', min=0, max=5)
                ]
            ),
            objectives=[
                Objective(name='y1', minimize=False),
                Objective(name='y2', minimize=False)
            ]
        )

        expected_pareto_df = pd.DataFrame(
            [
                [1, 2],
                [1, 2],
                [2, 1],
                [0.5, 2],
                [1, 1],
                [2, 0.5]
            ],
            columns=['y1', 'y2']
        )

        dominated_df = pd.DataFrame(
            [
                [0.5, 0.5],
                [0.5, 1],
                [0.5, 1.5],
                [1, 0.5],
                [1.5, 0.5]
            ],
            columns=['y1', 'y2']
        )

        all_objectives_df = pd.concat([dominated_df, expected_pareto_df])
        computed_pareto_df = ParetoFrontier.compute_pareto(optimization_problem, all_objectives_df)
        assert computed_pareto_df.sort_values(by=['y1','y2']).equals(expected_pareto_df.sort_values(by=['y1', 'y2']))
