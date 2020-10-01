#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Spaces import CategoricalDimension, ContinuousDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore

from .UtilityFunctionOptimizers.RandomSearchOptimizer import RandomSearchOptimizer, random_search_optimizer_config_store
from .UtilityFunctionOptimizers.GlowWormSwarmOptimizer import GlowWormSwarmOptimizer, glow_worm_swarm_optimizer_config_store
from .UtilityFunctions.ConfidenceBoundUtilityFunction import ConfidenceBoundUtilityFunction, confidence_bound_utility_function_config_store


experiment_designer_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name='experiment_designer_config',
        dimensions=[
            CategoricalDimension('utility_function_implementation', values=[ConfidenceBoundUtilityFunction.__name__]),
            CategoricalDimension('numeric_optimizer_implementation', values=[RandomSearchOptimizer.__name__, GlowWormSwarmOptimizer.__name__]),
            ContinuousDimension('fraction_random_suggestions', min=0, max=1)
        ]
    ).join(
        subgrid=confidence_bound_utility_function_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('utility_function_implementation', values=[ConfidenceBoundUtilityFunction.__name__])
    ).join(
        subgrid=random_search_optimizer_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('numeric_optimizer_implementation', values=[RandomSearchOptimizer.__name__])
    ).join(
        subgrid=glow_worm_swarm_optimizer_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('numeric_optimizer_implementation', values=[GlowWormSwarmOptimizer.__name__])
    ),
    default=Point(
        utility_function_implementation=ConfidenceBoundUtilityFunction.__name__,
        numeric_optimizer_implementation=RandomSearchOptimizer.__name__,
        confidence_bound_utility_function_config=confidence_bound_utility_function_config_store.default,
        random_search_optimizer_config=random_search_optimizer_config_store.default,
        fraction_random_suggestions=0.5
    )
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
            designer_config: Point,
            optimization_problem: OptimizationProblem,
            surrogate_model: RegressionModel,
            logger=None
    ):
        assert designer_config in experiment_designer_config_store.parameter_space

        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.config = designer_config
        self.optimization_problem = optimization_problem
        self.surrogate_model = surrogate_model
        self.rng = np.random.Generator(np.random.PCG64())

        self.utility_function = ConfidenceBoundUtilityFunction(
            function_config=self.config.confidence_bound_utility_function_config,
            surrogate_model=self.surrogate_model,
            minimize=self.optimization_problem.objectives[0].minimize,
            logger=self.logger
        )

        if self.config.numeric_optimizer_implementation == RandomSearchOptimizer.__name__:
            self.numeric_optimizer = RandomSearchOptimizer(
                optimizer_config=self.config.random_search_optimizer_config,
                optimization_problem=self.optimization_problem,
                utility_function=self.utility_function,
                logger=self.logger
            )
        elif self.config.numeric_optimizer_implementation == GlowWormSwarmOptimizer.__name__:
            self.numeric_optimizer = GlowWormSwarmOptimizer(
                optimizer_config=self.config.glow_worm_swarm_optimizer_config,
                optimization_problem=self.optimization_problem,
                utility_function=self.utility_function,
                logger=self.logger
            )

    def suggest(self, context_values_dataframe=None, random=False):
        self.logger.debug(f"Suggest(random={random})")
        random_number = self.rng.random()
        override_random = random_number < self.config.fraction_random_suggestions
        random = random or override_random
        if random:
            return self.optimization_problem.parameter_space.random()
        return self.numeric_optimizer.suggest(context_values_dataframe)
