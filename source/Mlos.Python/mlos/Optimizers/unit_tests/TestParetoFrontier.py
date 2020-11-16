#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import pytest

import numpy as np
import pandas as pd

from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, DiscreteDimension


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
            (random_objectives_df.loc[non_pareto_index] < row).any(axis=1).sum() == len(non_pareto_index)

            # Let's also make sure that no point on the pareto is dominated by any other point there.
            #
            other_rows = pareto_df.index.difference([i])
            assert (pareto_df.loc[other_rows] > row).all(axis=1).sum() == 0


    @pytest.mark.parametrize("minimize", [True, False])
    @pytest.mark.parametrize("num_output_dimensions", [2, 10])
    @pytest.mark.parametrize("num_points", [100, 10000])
    def test_hyperspheres(self, minimize, num_output_dimensions, num_points):
        """Use polar coordinates to generate cartesian coordinates of points on the surface and interior of a hypershpere.

        The idea is that we can know which points are optimal upfront.

        :param self:
        :return:
        """
        max_radius = 10

        parameter_dimensions = [
            ContinuousDimension(name="radius", min=0, max=max_radius)
        ]

        for i in range(1, num_output_dimensions):
            if minimize:
                parameter_dimensions.append(ContinuousDimension(name=f"theta{i}", min=math.pi, max=math.pi * 1.5))
            else:
                parameter_dimensions.append(ContinuousDimension(name=f"theta{i}", min=0, max=math.pi / 2))

        parameter_space = SimpleHypergrid(
            name='polar_coordinates',
            dimensions=parameter_dimensions
        )

        objective_space = SimpleHypergrid(
            name='rectangular_coordinates',
            dimensions=[
                ContinuousDimension(name=f"y{i}", min=0, max=max_radius)
                for i in range(num_output_dimensions)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=parameter_space,
            objective_space=objective_space,
            objectives=[Objective(name=f'y{i}', minimize=minimize) for i in range(num_output_dimensions)]
        )

        random_params_df = optimization_problem.feature_space.random_dataframe(num_points)

        # Let's randomly subsample 10% of points in random_params_df and make those points pareto optimal.
        #
        optimal_points_index = random_params_df.sample(
            frac=0.1,
            replace=False,
            axis='index'
        ).index

        random_params_df.loc[optimal_points_index, ['polar_coordinates.radius']] = max_radius

        objectives_df = pd.DataFrame({'y0': random_params_df['polar_coordinates.radius'] * np.cos(random_params_df['polar_coordinates.theta1'])})

        for i in range(1, num_output_dimensions):
            objectives_df[f'y{i}'] = random_params_df['polar_coordinates.radius'] * np.sin(random_params_df[f'polar_coordinates.theta{i}'])


        pareto_df = ParetoFrontier.compute_pareto(
            optimization_problem=optimization_problem,
            objectives_df=objectives_df
        )

        # We know that all of the pareto efficient points must be on the frontier.
        #
        assert pareto_df.index.intersection(optimal_points_index).difference(optimal_points_index).empty
