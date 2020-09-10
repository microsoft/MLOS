#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Logger import create_logger
from mlos.Tracer import trace
from mlos.Spaces import SimpleHypergrid, DiscreteDimension, Point, DefaultConfigMeta

from mlos.Optimizers.OptimizationProblem import OptimizationProblem


class RandomSearchOptimizerConfig(metaclass=DefaultConfigMeta):
    CONFIG_SPACE = SimpleHypergrid(
        name="random_search_optimizer_config",
        dimensions=[
            DiscreteDimension(name="num_samples_per_iteration", min=1, max=1000)
        ]
    )

    _DEFAULT = Point(
        num_samples_per_iteration=1000
    )

    @classmethod
    def create_from_config_point(cls, config_point):
        config_key_value_pairs = {param_name: value for param_name, value in config_point}
        return cls(**config_key_value_pairs)

    def __init__(self, num_samples_per_iteration=_DEFAULT.num_samples_per_iteration):
        self.num_samples_per_iteration = num_samples_per_iteration


class RandomSearchOptimizer:
    """ Performs a random search over the search space.

    This is the simplest optimizer to implement and a good baseline for all other optimizers
    to beat.

    """

    def __init__(
            self,
            optimizer_config: RandomSearchOptimizerConfig,
            optimization_problem: OptimizationProblem,
            utility_function,
            logger=None
    ):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger
        self.optimization_problem = optimization_problem
        self.utility_function = utility_function
        self.config = optimizer_config

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
        config_values_dataframe = self.optimization_problem.parameter_space.random_dataframe(num_samples=self.config.num_samples_per_iteration)
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

    @trace()
    def suggest(self, context_values_dataframe=None):
        """ Returns the next best configuration to try.

        It does so by generating num_samples_per_iteration random configurations,
        passing them through the utility function and selecting the configuration with
        the highest utility value.
        """
        config_to_suggest = self.maximize(self.utility_function, context_values_dataframe=context_values_dataframe)
        self.logger.debug(f"Suggesting: {str(config_to_suggest)}")
        return config_to_suggest
