#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
import pandas as pd

from mlos.Logger import create_logger
from mlos.Tracer import trace
from mlos.Spaces import SimpleHypergrid, DiscreteDimension, Point

from mlos.Optimizers.OptimizationProblem import OptimizationProblem


class RandomSearchOptimizerConfig:
    CONFIG_SPACE = SimpleHypergrid(
        name="random_search_optimizer_config",
        dimensions=[
            DiscreteDimension(name="num_samples_per_iteration", min=1, max=1000)
        ]
    )

    DEFAULT = Point(
        num_samples_per_iteration=1000
    )

    @classmethod
    def create_from_config_point(cls, config_point):
        config_key_value_pairs = {param_name: value for param_name, value in config_point}
        return cls(**config_key_value_pairs)

    def __init__(self, num_samples_per_iteration=DEFAULT.num_samples_per_iteration):
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
    def suggest(self, context_values_dataframe=None):  # pylint: disable=unused-argument
        """ Returns the next best configuration to try.

        It does so by generating num_samples_per_iteration random configurations,
        passing them through the utility function and selecting the configuration with
        the highest utility value.

        TODO: make it capable of consuming the context values
        :return:
        """
        parameter_names = [
            dimension.name
            for dimension
            in self.optimization_problem.parameter_space.dimensions
        ]

        candidate_configs = []

        for _ in range(self.config.num_samples_per_iteration):
            candidate_config = self.optimization_problem.parameter_space.random()
            candidate_configs.append(candidate_config)

        # Let's build a dictionary to create a dataframe
        data_dict = {}
        for parameter_name in parameter_names:
            parameter_values_per_candidate = []
            for candidate_config in candidate_configs:
                if parameter_name in candidate_config:
                    parameter_values_per_candidate.append(candidate_config[parameter_name])
                else:
                    parameter_values_per_candidate.append(np.NaN)
            data_dict[parameter_name] = parameter_values_per_candidate

        feature_values_dataframe = pd.DataFrame(data_dict)

        utility_function_values = self.utility_function(feature_values_dataframe)
        index_of_max_value = utility_function_values.index(max(utility_function_values))
        config_to_suggest = candidate_configs[index_of_max_value]
        self.logger.debug(f"Suggesting: {str(config_to_suggest)}")
        return config_to_suggest
