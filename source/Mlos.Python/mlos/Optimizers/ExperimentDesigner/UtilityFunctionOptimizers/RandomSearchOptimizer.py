#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd

from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.UtilityFunctionOptimizer import UtilityFunctionOptimizer
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.UtilityFunction import UtilityFunction
from mlos.Spaces import SimpleHypergrid, DiscreteDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore
from mlos.Tracer import trace


random_search_optimizer_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="random_search_optimizer_config",
        dimensions=[
            DiscreteDimension(name="num_samples_per_iteration", min=1, max=100000)
        ]
    ),
    default=Point(
        num_samples_per_iteration=1000
    )
)


class RandomSearchOptimizer(UtilityFunctionOptimizer):
    """ Performs a random search over the search space.

    This is the simplest optimizer to implement and a good baseline for all other optimizers
    to beat.

    """

    def __init__(
            self,
            optimizer_config: Point,
            optimization_problem: OptimizationProblem,
            utility_function: UtilityFunction,
            logger=None
    ):
        UtilityFunctionOptimizer.__init__(self, optimizer_config, optimization_problem, utility_function, logger)

    @trace()
    def maximize(self, target_function, context_values_dataframe=None):
        """Maximize callable target function.

        Parameters
        ----------
        target_function : callable
            Function to maximize.
        context_values_dataframe : DataFrame (default=None)
            Context for optimization.

        Returns
        -------
        position_of_optimum : Point
        """
        config_values_dataframe = self.optimization_problem.parameter_space.random_dataframe(num_samples=self.optimizer_config.num_samples_per_iteration)
        if context_values_dataframe is not None:
            assert len(context_values_dataframe) == 1
            config_values_dataframe['_join_key'] = 0
            copied_context = context_values_dataframe.copy()
            copied_context['_join_key'] = 0
            feature_values_dataframe = config_values_dataframe.merge(copied_context, how='outer').drop(columns='_join_key')
            config_values_dataframe = config_values_dataframe.drop(columns='_join_key')
        else:
            feature_values_dataframe = config_values_dataframe
        target_values = target_function(feature_values_dataframe.copy(deep=False))
        num_target_values = len(target_values)
        index_of_max_value = target_values.argmax() if num_target_values > 0 else 0
        return Point.from_dataframe(config_values_dataframe.iloc[[index_of_max_value]])

