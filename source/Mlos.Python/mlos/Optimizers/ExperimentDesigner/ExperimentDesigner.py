#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Logger import create_logger
from mlos.Spaces import CategoricalDimension, Point, SimpleHypergrid
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel
from mlos.Optimizers.OptimizationProblem import OptimizationProblem

from .UtilityFunctions.ConfidenceBoundUtilityFunction import ConfidenceBoundUtilityFunction, ConfidenceBoundUtilityFunctionConfig
from .NumericOptimizers.RandomSearchOptimizer import RandomSearchOptimizer, RandomSearchOptimizerConfig



class ExperimentDesignerConfig:

    CONFIG_SPACE = SimpleHypergrid(
        name='experiment_designer_config',
        dimensions=[
            CategoricalDimension('utility_function_implementation', values=[ConfidenceBoundUtilityFunction.__name__]),
            CategoricalDimension('numeric_optimizer_implementation', values=[RandomSearchOptimizer.__name__])
        ]
    ).join(
        subgrid=ConfidenceBoundUtilityFunctionConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension('utility_function_implementation', values=[ConfidenceBoundUtilityFunction.__name__])
    ).join(
        subgrid=RandomSearchOptimizerConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension('numeric_optimizer_implementation', values=[RandomSearchOptimizer.__name__])
    )

    DEFAULT = Point(
        utility_function_implementation=ConfidenceBoundUtilityFunction.__name__,
        numeric_optimizer_implementation=RandomSearchOptimizer.__name__,
        confidence_bound_utility_function_config=ConfidenceBoundUtilityFunctionConfig.DEFAULT,
        random_search_optimizer_config=RandomSearchOptimizerConfig.DEFAULT
    )


class ExperimentDesigner:
    """ Portion of a BayesianOptimizer concerned with Design of Experiments.

    The two main components of a Bayesian Optimizer are:
    * the surrogate model - responsible for fitting a regression function to try to predict some performance metric(s)
        based on suggested config, and context information
    * the experiment designer - responsible for suggesting the next configuration to try against the real system.

    The experiment designer can be parameterized by the following:
        1. The utility function - the surrogate model predicts performance (with uncertainty) for any given config.
            The utility function indicates the value (or in other words: utility) of the predicted performance.

        2. Utility function maximizer - being able to compute the utility function is insufficient. We must be able to
            select a configuration that maximizes the utility function and to do that, we need an optimizer.
            One way to think about it is to imagine a baby optimizer inside the big bayesian optimizer.

    """

    def __init__(
            self,
            designer_config: ExperimentDesignerConfig,
            optimization_problem: OptimizationProblem,
            surrogate_model: RegressionModel,
            logger=None
    ):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.config = designer_config
        self.optimization_problem = optimization_problem
        self.surrogate_model = surrogate_model

        assert self.config.utility_function_implementation == ConfidenceBoundUtilityFunction.__name__
        self.utility_function = ConfidenceBoundUtilityFunction(
            function_config=ConfidenceBoundUtilityFunctionConfig.create_from_config_point(self.config.confidence_bound_utility_function_config),
            surrogate_model=self.surrogate_model,
            minimize=self.optimization_problem.objectives[0].minimize,
            logger=self.logger
        )

        assert self.config.numeric_optimizer_implementation == RandomSearchOptimizer.__name__
        self.numeric_optimizer = RandomSearchOptimizer(
            optimizer_config=RandomSearchOptimizerConfig.create_from_config_point(self.config.random_search_optimizer_config),
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            logger=self.logger
        )

    def suggest(self, context_values_dataframe=None, random=False):
        self.logger.debug(f"Suggest(random={random})")
        if random:
            return self.optimization_problem.parameter_space.random()
        return self.numeric_optimizer.suggest(context_values_dataframe)
