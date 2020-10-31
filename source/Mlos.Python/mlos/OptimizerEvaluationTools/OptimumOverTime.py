#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd

from mlos.Optimizers.OptimumDefinition import OptimumDefinition
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Spaces import Point

class OptimumOverTime:
    """Keeps track of a single definition of optimum over time.

    """
    def __init__(
        self,
        optimization_problem: OptimizationProblem,
        optimum_definition: OptimumDefinition,
        alpha: float = 0.05
    ):
        self.optimization_problem = optimization_problem
        self.optimum_definition = optimum_definition
        self.alpha = alpha
        self._iteration_numbers = []
        self._optimal_configs = []
        self._optimum_values = []

    def add_optimum_at_iteration(self, iteration: int, optimum_config: Point, optimum_value: Point):
        assert optimum_config in self.optimization_problem.parameter_space

        self._iteration_numbers.append(iteration)
        self._optimal_configs.append(optimum_config)
        self._optimum_values.append(optimum_value)

    def get_dataframe(self) -> pd.DataFrame:
        assert len(self._iteration_numbers) == len(self._optimal_configs) == len(self._optimum_values)

        iteration_df = pd.DataFrame({'iteration': self._iteration_numbers})

        config_dicts = [config.to_dict() for config in self._optimal_configs]
        config_df = pd.DataFrame(config_dicts)

        optimum_dicts = [optimum.to_dict() for optimum in self._optimum_values]
        optimum_df = pd.DataFrame(optimum_dicts)

        combined_df = pd.concat([iteration_df, config_df, optimum_df], axis=1)
        return combined_df


    def get_last_optimum(self):
        if len(self._optimal_configs) > 0 and len(self._optimum_values) > 0:
            return self._optimal_configs[-1], self._optimum_values[-1]
        else:
            raise ValueError("No optima were added.")


