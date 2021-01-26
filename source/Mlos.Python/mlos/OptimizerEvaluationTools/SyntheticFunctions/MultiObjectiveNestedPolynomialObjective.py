#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math

import pandas as pd

from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase
from mlos.OptimizerEvaluationTools.SyntheticFunctions.NestedPolynomialObjective import NestedPolynomialObjective, nested_polynomial_objective_config_space
from mlos.Optimizers.OptimizationProblem import Objective, OptimizationProblem
from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Hypergrid, Point, SimpleHypergrid
from mlos.Utils.KeyOrderedDict import KeyOrderedDict

multi_objective_nested_polynomial_config_space = SimpleHypergrid(
    name="multi_objective_nested_polynomial_config",
    dimensions=[
        DiscreteDimension(name="num_objectives", min=1, max=10),
        CategoricalDimension(name="objective_function_implementation", values=[NestedPolynomialObjective.__name__])
    ]
).join(
    subgrid=nested_polynomial_objective_config_space,
    on_external_dimension=CategoricalDimension(name="objective_function_implementation", values=[NestedPolynomialObjective.__name__])
)

class MultiObjectiveNestedPolynomialObjective(ObjectiveFunctionBase):
    """A multi-objective function where each objective is a separate NestedPolynomialObjective.
    """

    def __init__(self, objective_function_config: Point):
        assert objective_function_config in multi_objective_nested_polynomial_config_space
        ObjectiveFunctionBase.__init__(self, objective_function_config)

        nested_polynomial_objective_config = objective_function_config.nested_polynomial_objective_config
        self._nested_polynomial_objective_config = nested_polynomial_objective_config
        self._ordered_output_dimension_names = [f'y{i}' for i in range(objective_function_config.num_objectives)]
        self._individual_objective_functions = KeyOrderedDict(ordered_keys=self._ordered_output_dimension_names, value_type=NestedPolynomialObjective)

        # Let's create the required number of objective functions.
        #
        for i in range(objective_function_config.num_objectives):
            nested_polynomial_objective_config.polynomial_objective_config.seed += i
            single_objective_function = NestedPolynomialObjective(objective_function_config=nested_polynomial_objective_config)
            self._individual_objective_functions[i] = single_objective_function

        self._parameter_space = self._individual_objective_functions[0].parameter_space


        self._output_space = SimpleHypergrid(
            name='output_space',
            dimensions=[
                ContinuousDimension(name=output_dim_name, min=-math.inf, max=math.inf)
                for output_dim_name in self._ordered_output_dimension_names
            ]
        )

        self.default_optimization_problem = OptimizationProblem(
            parameter_space=self._parameter_space,
            objective_space=self._output_space,
            objectives=[
                Objective(name=name, minimize=True)
                for name in self._ordered_output_dimension_names
            ]
        )

    @property
    def parameter_space(self) -> Hypergrid:
        return self._parameter_space

    @property
    def output_space(self) -> Hypergrid:
        return self._output_space

    def evaluate_point(self, point: Point) -> Point:
        values = {
            dim_name: individual_objective_function.evaluate_point(point)['y']
            for dim_name, individual_objective_function
            in self._individual_objective_functions
        }
        return Point(**values)

    def evaluate_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        results_df = pd.DataFrame()
        for dim_name, individual_objective_function in self._individual_objective_functions:
            single_objective_df = individual_objective_function.evaluate_dataframe(dataframe)
            results_df[dim_name] = single_objective_df['y']
        return results_df

    def get_context(self) -> Point:
        """ Returns the config used to create the polynomial.
        Down the road it could return some more info about the resulting polynomial.
        :return:
        """
        return self.objective_function_config
