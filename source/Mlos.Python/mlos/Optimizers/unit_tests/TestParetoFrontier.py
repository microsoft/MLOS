#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import pytest
import random
from typing import List

import matplotlib.pyplot as plt

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


    @pytest.mark.parametrize("minimize", ["all", "none", "some"])
    @pytest.mark.parametrize("num_output_dimensions", [2])
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

        # Keep track of which objectives to minimize.
        #
        minimize_by_objective: List[bool] = []

        for i in range(num_output_dimensions):
            if minimize == "all":
                minimize_this_objective = True
            elif minimize == "none":
                minimize_this_objective = False
            elif minimize == "some":
                # Alternate between first and third quarters.
                #
                minimize_this_objective = ((i % 2) == 1)
            else:
                assert False

            minimize_by_objective.append(minimize_this_objective)

            if minimize_this_objective:
                minimum = math.pi
                maximum = math.pi * 1.5
            else:
                minimum = 0
                maximum = math.pi / 2

            if i == 0:
                continue

            parameter_dimensions.append(ContinuousDimension(name=f"theta{i}", min=minimum, max=maximum))


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
            objectives=[Objective(name=f'y{i}', minimize=minimize_objective) for i, minimize_objective in enumerate(minimize_by_objective)]
        )

        optimization_problem.feature_space.random_state = random.Random(42)
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

        if not optimal_points_index.difference(pareto_df.index.intersection(optimal_points_index)).empty:
            objectives_df_copy = objectives_df.copy(deep=True)
            objectives_df_copy['y1'] = -objectives_df_copy['y1']
            objectives_df.plot.scatter("y0", "y1")
            objectives_df_copy.plot.scatter("y0", "y1")
            objectives_df.loc[optimal_points_index].plot.scatter("y0", "y1")
            pareto_df.plot.scatter("y0", "y1", marker='x')
            plt.show()

        # We know that all of the pareto efficient points must be on the frontier.
        #
        assert optimal_points_index.difference(pareto_df.index.intersection(optimal_points_index)).empty
        assert len(pareto_df.index) >= len(optimal_points_index)

    @pytest.mark.parametrize("minimize", ["all", "none", "some"])
    @pytest.mark.parametrize("num_output_dimensions", [2])
    @pytest.mark.parametrize("num_points", [100, 10000])
    def test_hyperspheres_2(self, minimize, num_output_dimensions, num_points):
        """Uses polar coordinates to generate cartesian coordinates of points on the surface and interior of a hypershpere.

        The idea is that we want to find a pareto frontier that optimizes the cartesian coordinates.
        By setting the radius of some of the points to the radius of the hypersphere, we guarantee that they are non-dominated.
        Such points must appear on the pareto frontier, though it's quite possible that other non-dominated points from the interior
        of the sphere could appear as well. The intuition in 2D is that we can draw a secant between two neighboring pareto efficient
        points on the perimeter. Any point that is between that secant and the perimeter is not dominated and would thus be pareto
        efficient as well. (Actually even more points are pareto efficient, but this subset is easiest to explain in text).


        We want to test scenarios where:
            1) all objectives are maximized,
            2) all objectives are minimized,
            3) some objectives are maximized and some are minimized.

        We want to be able to do that for an arbitrary number of dimensions so as to extract maximum coverage from this simple test.


        How the test works?
        -------------------
        For N objectives we will specify the following parameters:
            1. radius - distance of a point from origin.
            2. theta0, theta1, ..., theta{i}, ..., theta{N-1} - angle between the radius segment and the and the hyperplane containing
                unit vectors along y0, y1, ..., y{i}

        And the following N objectives that are computed from parameters:
            y0      = radius * cos(theta0)
            y1      = radius * sin(theta0) * cos(theta1)
            y2      = radius * sin(theta0) * sin(theta1) * cos(theta2)
            y3      = radius * sin(theta0) * sin(theta1) * sin(theta2) * cos(theta3)
            ...
            y{N-2}  = radius * sin(theta0) * sin(theta1) * ... * sin(theta{n-1}) * cos(thetaN)
            y{N-1}  = radius * sin(theta0) * sin(theta1) * ... * sin(theta{n-1}) * sin(thetaN)
                                                                                    ^ !! sin instead of cos !!

        1) Maximizing all objectives.
            To maximize all objectives we need to be them to be non-negative. In such as setup all points with r == sphere_radius
            will be pareto efficient. And we can assert that the computed pareto frontier contains them.

            This can be guaranteed, by keeping all angles theta in the first quadrant (0 .. pi/2) since both sin and cos are
            positive there. Thus their product will be too.

        2) Minimizing all objectives.
            Similarily, to minimize all objectives we need them to be non-positive. In such a setup we know that all points with
            r == sphere_radius are pareto efficient and we can assert that they are returned in the computation.

            We observe that all objectives except for the last one contain any number of sin factors and a single cosine factor.
            Cosine is guaranteed to be negative in the second quadrant (pi/2 .. pi) and sine is guaranteed to be positive there.
            So keeping all thetas in the range [pi/2 .. pi] makes all objectives negative except for the last one (which we can
            simply flip manually)

        3) Maximizing some objectives while minimizing others.
            We can take advantage of the fact that every second objective has an odd number of sin factors, whilst the rest has
            has an even number (again, except for the last one). So if we keep all sin factors negative, and all the cos factors
            positive, we get a neat situation of alternating objectives` signs.

            This is true in the fourth quadrant (3 * pi / 2 .. 2 * pi), where sin values are negative, and cos values are positive.

            The last objective - y{N-1} - will have N negative terms, so it will be positive if (N % 2) == 0 and negative otherwise.
            In other words:
                if (N % 2) == 0:
                    maximize y{N-1}
                else:
                    minimize y{N-1}


        :param self:
        :return:
        """
        hypersphere_radius = 10

        parameter_dimensions = [
            ContinuousDimension(name="radius", min=0, max=hypersphere_radius)
        ]

        if minimize == "all":
            # Let's keep angles in second quadrant.
            #
            theta_min = math.pi / 2
            theta_max = math.pi

        elif minimize == "none":
            # Let's keep all angles in the first quadrant.
            #


        # Keep track of which objectives to minimize.
        #
        minimize_mask: List[bool] = []

        for i in range(num_output_dimensions):
            if minimize == "all":
                minimize_this_objective = True



            elif minimize == "none":
                minimize_this_objective = False


            elif minimize == "some":
                # Alternate between first and third quarters. Let's minimize odd ones, that way the y{N-1} doesn't require a sign flip.
                #
                minimize_this_objective = ((i % 2) == 1)
            else:
                assert False

            minimize_mask.append(minimize_this_objective)

            if minimize_this_objective:
                minimum = math.pi
                maximum = math.pi * 1.5
            else:
                minimum = 0
                maximum = math.pi / 2


            parameter_dimensions.append(ContinuousDimension(name=f"theta{i}", min=minimum, max=maximum))

        parameter_space = SimpleHypergrid(
            name='polar_coordinates',
            dimensions=parameter_dimensions
        )

        objective_space = SimpleHypergrid(
            name='rectangular_coordinates',
            dimensions=[
                ContinuousDimension(name=f"y{i}", min=0, max=hypersphere_radius)
                for i in range(num_output_dimensions)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=parameter_space,
            objective_space=objective_space,
            objectives=[Objective(name=f'y{i}', minimize=minimize_objective) for i, minimize_objective in
                        enumerate(minimize_mask)]
        )

        optimization_problem.feature_space.random_state = random.Random(42)
        random_params_df = optimization_problem.feature_space.random_dataframe(num_points)

        # Let's randomly subsample 10% of points in random_params_df and make those points pareto optimal.
        #
        optimal_points_index = random_params_df.sample(
            frac=0.1,
            replace=False,
            axis='index'
        ).index

        random_params_df.loc[optimal_points_index, ['polar_coordinates.radius']] = hypersphere_radius

        objectives_df = pd.DataFrame(
            {'y0': random_params_df['polar_coordinates.radius'] * np.cos(random_params_df['polar_coordinates.theta1'])})

        for i in range(1, num_output_dimensions):
            objectives_df[f'y{i}'] = random_params_df['polar_coordinates.radius'] * np.sin(
                random_params_df[f'polar_coordinates.theta{i}'])

        pareto_df = ParetoFrontier.compute_pareto(
            optimization_problem=optimization_problem,
            objectives_df=objectives_df
        )

        if not optimal_points_index.difference(pareto_df.index.intersection(optimal_points_index)).empty:
            objectives_df_copy = objectives_df.copy(deep=True)
            objectives_df_copy['y1'] = -objectives_df_copy['y1']
            objectives_df.plot.scatter("y0", "y1")
            objectives_df_copy.plot.scatter("y0", "y1")
            objectives_df.loc[optimal_points_index].plot.scatter("y0", "y1")
            pareto_df.plot.scatter("y0", "y1", marker='x')
            plt.show()

        # We know that all of the pareto efficient points must be on the frontier.
        #
        assert optimal_points_index.difference(pareto_df.index.intersection(optimal_points_index)).empty
        assert len(pareto_df.index) >= len(optimal_points_index)

