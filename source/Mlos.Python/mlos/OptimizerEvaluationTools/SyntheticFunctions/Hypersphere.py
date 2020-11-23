#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math

import numpy as np
import pandas as pd

from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase
from mlos.Optimizers.OptimizationProblem import Objective, OptimizationProblem
from mlos.Spaces import ContinuousDimension, Hypergrid, Point, SimpleHypergrid

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

        self.num_objectives = self.objective_function_config.num_objectives
        self.radius = self.objective_function_config.radius
        self.minimize = self.objective_function_config.minimize

        # Let's figure out the quadrant and which objectives to minimize.
        #
        if self.minimize == "all":
            # Let's keep angles in second quadrant.
            #
            self.theta_min = math.pi / 2
            self.theta_max = math.pi
            self.minimize_mask = [True for _ in range(self.num_objectives)]

        elif self.minimize == "none":
            # Let's keep all angles in the first quadrant.
            #
            self.theta_min = 0
            self.theta_max = math.pi / 2
            self.minimize_mask = [False for _ in range(self.num_objectives)]

        elif self.objective_function_config.minimize == "some":
            # Let's keep all angles in the fourth quadrant.
            #
            self.theta_min = 1.5 * math.pi
            self.theta_max = 2 * math.pi

            # Let's minimize odd ones, that way the y{N-1} doesn't require a sign flip.
            #
            self.minimize_mask = [(i % 2) == 1 for i in range(self.num_objectives)]

        else:
            assert False

        # Let's put together the optimization problem.
        #
        parameter_dimensions = [ContinuousDimension(name="radius", min=0, max=self.radius)]
        for i in range(self.num_objectives):
            parameter_dimensions.append(ContinuousDimension(name=f"theta{i}", min=self.theta_min, max=self.theta_max))

        self._parameter_space = SimpleHypergrid(
            name='spherical_coordinates',
            dimensions=parameter_dimensions
        )

        objective_dimensions = []
        for i, minimize in enumerate(self.minimize_mask):
            if minimize:
                objective_dimensions.append(ContinuousDimension(name=f"y{i}", min=-self.radius, max=0))
            else:
                objective_dimensions.append(ContinuousDimension(name=f"y{i}", min=0, max=self.radius))

        self._objective_space = SimpleHypergrid(
            name='rectangular_coordinates',
            dimensions=objective_dimensions
        )

        # TODO: add this to the ObjectiveFunctionBase interface.
        #
        self.default_optimization_problem = OptimizationProblem(
            parameter_space=self._parameter_space,
            objective_space=self._objective_space,
            objectives=[
                Objective(name=f'y{i}', minimize=minimize_objective)
                for i, minimize_objective
                in enumerate(self.minimize_mask)
            ]
        )


    @property
    def parameter_space(self) -> Hypergrid:
        return self._parameter_space

    @property
    def output_space(self) -> Hypergrid:
        return self._objective_space


    def evaluate_dataframe(self, dataframe: pd.DataFrame):
        # We can compute our objectives more efficiently, by maintaining a prefix of r * sin(theta0) * ... * sin(theta{i-1})
        #
        prefix = dataframe['radius']
        objectives_df = pd.DataFrame()
        for i in range(self.num_objectives - 1):
            objectives_df[f'y{i}'] = prefix * np.cos(dataframe[f'theta{i}'])
            prefix = prefix * np.sin(dataframe[f'theta{i}'])

        # Conveniently, by the time the loop exits, the prefix is the value of our last objective.
        #
        if self.minimize == "all":
            # Must flip the prefix first, since there was no negative cosine to do it for us.
            #
            objectives_df[f'y{self.num_objectives - 1}'] = -prefix
        else:
            objectives_df[f'y{self.num_objectives - 1}'] = prefix

        return objectives_df

    def get_context(self) -> Point:
        """ Returns a context value for this objective function.

        If the context changes on every invokation, this should return the latest one.
        :return:
        """
        return Point(radius=self.radius)
