#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod
import pandas as pd
from mlos.Logger import create_logger
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.UtilityFunction import UtilityFunction
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Spaces import Point

class UtilityFunctionOptimizer(ABC):
    """ Interface to be implemented by all numeric optimizers.

    """

    def __init__(
            self,
            optimizer_config: Point,
            optimization_problem: OptimizationProblem,
            utility_function: UtilityFunction,
            logger=None
    ):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger
        self.optimizer_config = optimizer_config
        self.optimization_problem = optimization_problem
        self.utility_function = utility_function

    def suggest(self, context_values_dataframe: pd.DataFrame) -> Point:
        config_to_suggest = self.maximize(lambda features: self.utility_function(features).utility,
                                          context_values_dataframe=context_values_dataframe)
        self.logger.debug(f"Suggesting: {str(config_to_suggest)}")
        return config_to_suggest

    @abstractmethod
    def maximize(self, target_function, context_values_dataframe=None):
        """Maximize the target function"""
        raise NotImplementedError