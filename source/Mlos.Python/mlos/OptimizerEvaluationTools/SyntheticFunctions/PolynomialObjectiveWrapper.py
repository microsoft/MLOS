#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math

import pandas as pd

from mlos.Spaces import ContinuousDimension, Hypergrid, Point, SimpleHypergrid
from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase
from mlos.OptimizerEvaluationTools.SyntheticFunctions.PolynomialObjective import PolynomialObjective

class PolynomialObjectiveWrapper(ObjectiveFunctionBase):
    """Wraps the PolynomialObjective to provide the interface defined in the ObjectiveFunctionBase.

    """

    def __init__(self, objective_function_config: Point, domain_name: str = None):
        assert objective_function_config in PolynomialObjective.CONFIG_SPACE
        ObjectiveFunctionBase.__init__(self, objective_function_config)
        self._polynomial_objective_config = objective_function_config
        self._polynomial_function = PolynomialObjective(
            seed=objective_function_config.seed,
            input_domain_dimension=objective_function_config.input_domain_dimension,
            max_degree=objective_function_config.max_degree,
            include_mixed_coefficients=objective_function_config.include_mixed_coefficients,
            percent_coefficients_zeroed=objective_function_config.percent_coefficients_zeroed,
            coefficient_domain_min=objective_function_config.coefficient_domain_min,
            coefficient_domain_width=objective_function_config.coefficient_domain_width,
            include_noise=objective_function_config.include_noise,
            noise_coefficient_of_variation=objective_function_config.noise_coefficient_of_variation,
        )

        if domain_name is None:
            domain_name = "domain"

        self._parameter_space = SimpleHypergrid(
            name=domain_name,
            dimensions=[
                ContinuousDimension(
                    name=f"x_{i}",
                    min=objective_function_config.input_domain_min,
                    max=objective_function_config.input_domain_min + objective_function_config.input_domain_width
                ) for i in range(objective_function_config.input_domain_dimension)
            ]
        )

        self._output_space = SimpleHypergrid(
            name='output_space',
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

    @property
    def parameter_space(self) -> Hypergrid:
        return self._parameter_space

    @property
    def output_space(self) -> Hypergrid:
        return self._output_space

    def evaluate_point(self, point: Point) -> Point:
        point = Point(**{dim_name: point[dim_name] for dim_name in self._parameter_space.dimension_names})
        y = self._polynomial_function.evaluate(point.to_dataframe().to_numpy())
        return Point(y=y[0])

    def evaluate_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe = dataframe[self._parameter_space.dimension_names]
        y = self._polynomial_function.evaluate(dataframe.to_numpy())
        return pd.DataFrame({'y': y})

    def get_context(self) -> Point:
        """ Returns the config used to create the polynomial.

        Down the road it could return some more info about the resulting polynomial.

        :return:
        """
        return self._polynomial_objective_config
