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

    @abstractmethod
    def suggest(self, context_values_dataframe: pd.DataFrame) -> Point:
        raise NotImplementedError
