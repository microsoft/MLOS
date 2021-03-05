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
from mlos.Utils.KeyOrderedDict import KeyOrderedDict

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
        random_objectives_df = objective_space.random_dataframe(num_rows)

        pareto_frontier = ParetoFrontier(optimization_problem=optimization_problem, objectives_df=random_objectives_df)
        pareto_df = pareto_frontier.pareto_df

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


        pareto_frontier = ParetoFrontier(
            optimization_problem=optimization_problem,
            objectives_df=objectives_df
        )
        pareto_df = pareto_frontier.pareto_df

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
        pareto_frontier = ParetoFrontier(optimization_problem, all_objectives_df)
        computed_pareto_df = pareto_frontier.pareto_df
        assert computed_pareto_df.sort_values(by=['y1','y2']).equals(expected_pareto_df.sort_values(by=['y1', 'y2']))

    def test_pareto_frontier_volume_simple(self):
        """A simple sanity test on the pareto frontier volume computations.
        """

        # Let's generate a pareto frontier in 2D. ALl points lay on a line y = 1 - x
        x = np.linspace(start=0, stop=1, num=100)
        y = 1 - x
        pareto_df = pd.DataFrame({'x': x, 'y': y})
        optimization_problem = OptimizationProblem(
            parameter_space=None,
            objective_space=SimpleHypergrid(
                name='objectives',
                dimensions=[
                    ContinuousDimension(name='x', min=0, max=1),
                    ContinuousDimension(name='y', min=0, max=1)
                ]
            ),
            objectives=[Objective(name='x', minimize=False), Objective(name='y', minimize=False)]
        )
        pareto_frontier = ParetoFrontier(optimization_problem, pareto_df)
        pareto_volume_estimator = pareto_frontier.approximate_pareto_volume(num_samples=1000000)
        lower_bound, upper_bound = pareto_volume_estimator.get_two_sided_confidence_interval_on_pareto_volume(alpha=0.05)
        print(lower_bound, upper_bound)
        assert 0.49 < lower_bound < upper_bound < 0.51


    @pytest.mark.parametrize("minimize", ["all", "none", "some"])
    @pytest.mark.parametrize("num_dimensions", [2, 3, 4, 5])
    def test_pareto_frontier_volume_on_hyperspheres(self, minimize, num_dimensions):
        """Uses a known formula for the volume of the hyperspheres to validate the accuracy of the pareto frontier estimate.

        :return:
        """
        hypersphere_radius = 10
        inscribed_hypersphere_radius = 7  # For computing lower bound on volume

        # In order to validate the estimates, we must know the allowable upper and lower bounds.
        # We know that the estimate should not be higher than the volume of the n-ball (ball in n-dimensions).
        # We can also come up with a lower bound, by computing a volume of a slightly smaller ball inscribed
        # into the hypersphere. Note that the volume of an n-ball can be computed recursively, so we keep track
        # of n-ball volumes in lower dimensions.

        upper_bounds_on_sphere_volume_by_num_dimensions = {}
        lower_bounds_on_sphere_volume_by_num_dimensions = {}

        # Compute the base cases for the recursion.
        #
        upper_bounds_on_sphere_volume_by_num_dimensions[2] = np.pi * (hypersphere_radius ** 2)
        upper_bounds_on_sphere_volume_by_num_dimensions[3] = (4 / 3) * np.pi * (hypersphere_radius ** 3)

        lower_bounds_on_sphere_volume_by_num_dimensions[2] = np.pi * (inscribed_hypersphere_radius ** 2)
        lower_bounds_on_sphere_volume_by_num_dimensions[3] = (4 / 3) * np.pi * (inscribed_hypersphere_radius ** 3)

        # Compute the recursive values.
        #
        for n in range(4, num_dimensions + 1):
            upper_bounds_on_sphere_volume_by_num_dimensions[n] = upper_bounds_on_sphere_volume_by_num_dimensions[n-2] * 2 * np.pi * (hypersphere_radius ** 2) / n
            lower_bounds_on_sphere_volume_by_num_dimensions[n] = lower_bounds_on_sphere_volume_by_num_dimensions[n-2] * 2 * np.pi * (inscribed_hypersphere_radius ** 2) / n

        objective_function_config = Point(
            implementation=Hypersphere.__name__,
            hypersphere_config=Point(
                num_objectives=num_dimensions,
                minimize=minimize,
                radius=hypersphere_radius
            )
        )
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config)
        parameter_space = objective_function.parameter_space

        num_points = max(4, num_dimensions)
        linspaces = []

        for dimension in parameter_space.dimensions:
            if dimension.name == 'radius':
                linspaces.append(np.array([hypersphere_radius]))
            else:
                linspaces.append(dimension.linspace(num_points))
        meshgrids = np.meshgrid(*linspaces)
        reshaped_meshgrids = [meshgrid.reshape(-1) for meshgrid in meshgrids]

        params_df = pd.DataFrame({
            dim_name: reshaped_meshgrids[i]
            for i, dim_name
            in enumerate(parameter_space.dimension_names)
        })

        objectives_df = objective_function.evaluate_dataframe(params_df)

        pareto_frontier = ParetoFrontier(optimization_problem=objective_function.default_optimization_problem, objectives_df=objectives_df)
        print("Num points in pareto frontier: ", len(objectives_df.index))
        assert len(pareto_frontier.pareto_df.index) == len(objectives_df.index)
        pareto_volume_estimator = pareto_frontier.approximate_pareto_volume(num_samples=1000000)
        ci_lower_bound, ci_upper_bound = pareto_volume_estimator.get_two_sided_confidence_interval_on_pareto_volume(alpha=0.05)

        lower_bound_on_pareto_volume = lower_bounds_on_sphere_volume_by_num_dimensions[num_dimensions] / (2**num_dimensions)
        upper_bound_on_pareto_volume = upper_bounds_on_sphere_volume_by_num_dimensions[num_dimensions] / (2**num_dimensions)
        print("True bounds:", lower_bound_on_pareto_volume, upper_bound_on_pareto_volume)
        print("CI bounds: ", ci_lower_bound, ci_upper_bound)
        assert lower_bound_on_pareto_volume <= ci_lower_bound <= ci_upper_bound <= upper_bound_on_pareto_volume


