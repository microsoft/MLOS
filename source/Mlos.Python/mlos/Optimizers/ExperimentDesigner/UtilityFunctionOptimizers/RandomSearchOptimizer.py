#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd

from mlos.Exceptions import UtilityValueUnavailableException
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
    def suggest(self, context_values_dataframe: pd.DataFrame = None):
        """ Returns the next best configuration to try.

        It does so by generating num_samples_per_iteration random configurations,
        passing them through the utility function and selecting the configuration with
        the highest utility value.

        TODO: make it capable of consuming the context values
        :return:
        """
        parameter_values_dataframe = self.optimization_problem.parameter_space.random_dataframe(num_samples=self.optimizer_config.num_samples_per_iteration)
        feature_values_dataframe = self.optimization_problem.construct_feature_dataframe(
            parameters_df=parameter_values_dataframe,
            context_df=context_values_dataframe,
            product=True
        )
        utility_function_values = self.utility_function(feature_values_pandas_frame=feature_values_dataframe.copy(deep=False))
        num_utility_function_values = len(utility_function_values.index)

        if num_utility_function_values == 0:
            raise UtilityValueUnavailableException(f"Utility function {self.utility_function.__class__.__name__} produced no values.")

        index_of_max_value = utility_function_values[['utility']].idxmax()['utility']
        argmax_point = Point.from_dataframe(feature_values_dataframe.loc[[index_of_max_value]])
        config_to_suggest = argmax_point[self.optimization_problem.parameter_space.name]
        self.logger.debug(f"Suggesting: {str(config_to_suggest)}")
        return config_to_suggest
