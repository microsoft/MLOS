#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import Point
from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase
from mlos.OptimizerEvaluationTools.ObjectiveFunctionConfigStore import objective_function_config_store
from mlos.OptimizerEvaluationTools.SyntheticFunctions.Flower import Flower
from mlos.OptimizerEvaluationTools.SyntheticFunctions.Hypersphere import Hypersphere
from mlos.OptimizerEvaluationTools.SyntheticFunctions.MultiObjectiveNestedPolynomialObjective import MultiObjectiveNestedPolynomialObjective
from mlos.OptimizerEvaluationTools.SyntheticFunctions.NestedPolynomialObjective import NestedPolynomialObjective
from mlos.OptimizerEvaluationTools.SyntheticFunctions.PolynomialObjective import PolynomialObjective
from mlos.OptimizerEvaluationTools.SyntheticFunctions.PolynomialObjectiveWrapper import PolynomialObjectiveWrapper
from mlos.OptimizerEvaluationTools.SyntheticFunctions.ThreeLevelQuadratic import ThreeLevelQuadratic


class ObjectiveFunctionFactory:
    """ Creates specialized instances of the abstract base class: ObjectiveFunctionBase.

    """

    @classmethod
    def create_objective_function(cls, objective_function_config: Point) -> ObjectiveFunctionBase:
        assert objective_function_config in objective_function_config_store.parameter_space

        if objective_function_config.implementation == PolynomialObjective.__name__:
            polynomial_objective_config = objective_function_config.polynomial_objective_config
            return PolynomialObjectiveWrapper(polynomial_objective_config)

        if objective_function_config.implementation == ThreeLevelQuadratic.__name__:
            return ThreeLevelQuadratic()

        if objective_function_config.implementation == Flower.__name__:
            return Flower()

        if objective_function_config.implementation == NestedPolynomialObjective.__name__:
            return NestedPolynomialObjective(objective_function_config.nested_polynomial_objective_config)

        if objective_function_config.implementation == Hypersphere.__name__:
            return Hypersphere(objective_function_config.hypersphere_config)

        if objective_function_config.implementation == MultiObjectiveNestedPolynomialObjective.__name__:
            return MultiObjectiveNestedPolynomialObjective(objective_function_config.multi_objective_nested_polynomial_config)

        raise ValueError(f"Can't instantiate an objective function with the following implementation: {objective_function_config.implementation}")
