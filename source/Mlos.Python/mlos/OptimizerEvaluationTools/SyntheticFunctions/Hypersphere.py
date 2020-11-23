#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
from typing import List

import numpy as np
import pandas as pd

from mlos.Spaces import ContinuousDimension, Hypergrid, Point, SimpleHypergrid
from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase

class Hypersphere(ObjectiveFunctionBase):
    """Multi-objective function that converts spherical coordinates to cartesian ones.

    The idea is that we want to find a pareto frontier that optimizes the cartesian coordinates
    of points defined using random spherical coordinates.

    By setting the radius of some of the points to the radius of the hypersphere, we guarantee
    that they are non-dominated. Such points must appear on the pareto frontier, though it's
    quite possible that other non-dominated points from the interior of the sphere could appear
    as well. The intuition in 2D is that we can draw a secant between two neighboring pareto
    efficient points on the perimeter. Any point that is between that secant and the perimeter
    is not dominated and would thus be pareto efficient as well. (Actually even more points
    are pareto efficient, but this subset is easiest to explain in text).


    We want to use this objective function to test scenarios where:
        1) all objectives are maximized,
        2) all objectives are minimized,
        3) some objectives are maximized and some are minimized.

    We want to be able to do that for an arbitrary number of dimensions so as to extract
    maximum coverage from this simple test.


    How the function works?
    -------------------
    For N objectives we will specify the following parameters:
        1. radius - distance of a point from origin.
        2. theta0, theta1, ..., theta{i}, ..., theta{N-1} - angle between the radius
            segment and the hyperplane containing unit vectors along y0, y1, ..., y{i-1}

    And the following N objectives that are computed from parameters:
        y0      = radius * cos(theta0)
        y1      = radius * sin(theta0) * cos(theta1)
        y2      = radius * sin(theta0) * sin(theta1) * cos(theta2)
        y3      = radius * sin(theta0) * sin(theta1) * sin(theta2) * cos(theta3)
        ...
        y{N-2}  = radius * sin(theta0) * sin(theta1) * ... * sin(theta{N-2}) * cos(theta{N-1})
        y{N-1}  = radius * sin(theta0) * sin(theta1) * ... * sin(theta{N-2}) * sin(theta{N-1})
                                                    !!! sin instead of cos !!! ^

    1) Maximizing all objectives.
        To maximize all objectives we need them to be non-negative. In such as setup
        all points with r == sphere_radius will be pareto efficient. And we can assert that
        the computed pareto frontier contains them.

        This can be guaranteed, by keeping all angles theta in the first quadrant (0 .. pi/2) since both sin and cos are
        positive there. Thus their product will be too.

    2) Minimizing all objectives.
        Similarly, to minimize all objectives we need them to be non-positive. In such
        a setup we know that all points with r == sphere_radius are pareto efficient and
        we can assert that they are returned in the computation.

        We observe that all objectives except for the last one contain any number of sin
        factors and a single cosine factor. Cosine is guaranteed to be negative in the
        second quadrant (pi/2 .. pi) and sine is guaranteed to be positive there.
        So keeping all thetas in the range [pi/2 .. pi] makes all objectives negative
        except for the last one (which we can simply flip manually).

    3) Maximizing some objectives while minimizing others.
        We can take advantage of the fact that every second objective has an odd number
        of sin factors, whilst the rest has an even number (again, except for the last
        one). So if we keep all sin factors negative, and all the cos factors positive, we
        get a neat situation of alternating objectives' signs.

        This is true in the fourth quadrant (3 * pi / 2 .. 2 * pi), where sin values are
        negative, and cos values are positive.

        The last objective - y{N-1} - will have N negative terms, so it will be positive if
        (N % 2) == 0 and negative otherwise.

        In other words:
            if (N % 2) == 0:
                maximize y{N-1}
            else:
                minimize y{N-1}

    """



    def __init__(self, objective_function_config: Point = None):
        ObjectiveFunctionBase.__init__(self, objective_function_config)

        # Let's figure out the quadrant and which objectives to minimize.
        #
        self.minimize_mask: List[bool] = []

        if self.objective_function_config.minimize == "all":
            # Let's keep angles in second quadrant.
            #
            theta_min = math.pi / 2
            theta_max = math.pi
            minimize_mask = [True for _ in range(self.objective_function_config.num_output_dimensions)]

        elif self.objective_function_config.minimize == "none":
            # Let's keep all angles in the first quadrant.
            #
            theta_min = 0
            theta_max = math.pi / 2
            minimize_mask = [False for _ in range(num_output_dimensions)]

        elif self.objective_function_config.minimize == "some":
            # Let's keep all angles in the fourth quadrant.
            #
            theta_min = 1.5 * math.pi
            theta_max = 2 * math.pi

            # Let's minimize odd ones, that way the y{N-1} doesn't require a sign flip.
            #
            minimize_mask = [(i % 2) == 1 for i in range(num_output_dimensions)]

        else:
            assert False

        # Let's put together the optimization problem.
        #
        parameter_dimensions = [ContinuousDimension(name="radius", min=0, max=hypersphere_radius)]
        for i in range(num_output_dimensions):
            parameter_dimensions.append(ContinuousDimension(name=f"theta{i}", min=theta_min, max=theta_max))

        parameter_space = SimpleHypergrid(
            name='spherical_coordinates',
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
            objectives=[Objective(name=f'y{i}', minimize=minimize_objective) for i, minimize_objective in enumerate(minimize_mask)]
        )


    @property
    def parameter_space(self) -> Hypergrid:
        return self._domain

    @property
    def output_space(self) -> Hypergrid:
        return self._range


    def evaluate_dataframe(self, dataframe: pd.DataFrame):
        a = 1
        b = 2
        c = 4
        x = dataframe.to_numpy()
        sum_of_squares = np.sum(x**2, axis=1)
        x_norm = np.sqrt(sum_of_squares)
        values = a * x_norm + b * np.sin(c * np.arctan2(x[:, 0], x[:, 1]))
        return pd.DataFrame({'y': values})


    def get_context(self) -> Point:
        """ Returns a context value for this objective function.

        If the context changes on every invokation, this should return the latest one.
        :return:
        """
        return Point()
