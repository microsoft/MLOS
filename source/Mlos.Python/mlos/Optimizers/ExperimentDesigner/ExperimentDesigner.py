#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np

from mlos.Exceptions import UnableToProduceGuidedSuggestionException
from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Spaces import CategoricalDimension, ContinuousDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore

from .UtilityFunctionOptimizers.RandomNearIncumbentOptimizer import RandomNearIncumbentOptimizer, random_near_incumbent_optimizer_config_store
from .UtilityFunctionOptimizers.RandomSearchOptimizer import RandomSearchOptimizer, random_search_optimizer_config_store
from .UtilityFunctionOptimizers.GlowWormSwarmOptimizer import GlowWormSwarmOptimizer, glow_worm_swarm_optimizer_config_store
from .UtilityFunctions.ConfidenceBoundUtilityFunction import ConfidenceBoundUtilityFunction, confidence_bound_utility_function_config_store
from .UtilityFunctions.MultiObjectiveProbabilityOfImprovementUtilityFunction import MultiObjectiveProbabilityOfImprovementUtilityFunction, \
    multi_objective_probability_of_improvement_utility_function_config_store

from .UtilityFunctionOptimizers.UtilityFunctionOtimizerFactory import UtilityFunctionOtimizerFactory


experiment_designer_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name='experiment_designer_config',
        dimensions=[
            CategoricalDimension('utility_function_implementation', values=[
                ConfidenceBoundUtilityFunction.__name__,
                MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__
            ]),
            CategoricalDimension('numeric_optimizer_implementation', values=[
                RandomSearchOptimizer.__name__,
                GlowWormSwarmOptimizer.__name__,
                RandomNearIncumbentOptimizer.__name__
            ]),
            ContinuousDimension('fraction_random_suggestions', min=0, max=1)
        ]
    ).join(
        subgrid=confidence_bound_utility_function_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('utility_function_implementation', values=[ConfidenceBoundUtilityFunction.__name__])
    ).join(
        subgrid=multi_objective_probability_of_improvement_utility_function_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('utility_function_implementation', values=[MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__])
    ).join(
        subgrid=random_search_optimizer_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('numeric_optimizer_implementation', values=[RandomSearchOptimizer.__name__])
    ).join(
        subgrid=glow_worm_swarm_optimizer_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('numeric_optimizer_implementation', values=[GlowWormSwarmOptimizer.__name__])
    ).join(
        subgrid=random_near_incumbent_optimizer_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('numeric_optimizer_implementation', values=[RandomNearIncumbentOptimizer.__name__])
    ),
    default=Point(
        utility_function_implementation=ConfidenceBoundUtilityFunction.__name__,
        numeric_optimizer_implementation=RandomSearchOptimizer.__name__,
        confidence_bound_utility_function_config=confidence_bound_utility_function_config_store.default,
        random_search_optimizer_config=random_search_optimizer_config_store.default,
        fraction_random_suggestions=0.5
    )
)

experiment_designer_config_store.add_config_by_name(
    config_name="default_random_near_incumbent_config",
    config_point=Point(
        utility_function_implementation=MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__,
        numeric_optimizer_implementation=RandomNearIncumbentOptimizer.__name__,
        multi_objective_probability_of_improvement_config=multi_objective_probability_of_improvement_utility_function_config_store.default,
        random_near_incumbent_optimizer_config=random_near_incumbent_optimizer_config_store.default,
        fraction_random_suggestions=0.5
    )
)

experiment_designer_config_store.add_config_by_name(
    config_name="default_glow_worm_config",
    config_point=Point(
        utility_function_implementation=ConfidenceBoundUtilityFunction.__name__,
        numeric_optimizer_implementation=GlowWormSwarmOptimizer.__name__,
        confidence_bound_utility_function_config=confidence_bound_utility_function_config_store.default,
        glow_worm_swarm_optimizer_config=glow_worm_swarm_optimizer_config_store.default,
        fraction_random_suggestions=0.5
    ),
    description="Experiment designer config with glow worm swarm optimizer as a utility function optimizer."
)


experiment_designer_config_store.add_config_by_name(
    config_name="default_multi_objective_config",
    config_point=Point(
        utility_function_implementation=MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__,
        numeric_optimizer_implementation=RandomSearchOptimizer.__name__,
        multi_objective_probability_of_improvement_config=multi_objective_probability_of_improvement_utility_function_config_store.default,
        random_search_optimizer_config=random_search_optimizer_config_store.default,
        fraction_random_suggestions=0.5
    ),
    description="Default optimizer for multi-objective optimization."
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
            surrogate_model: MultiObjectiveRegressionModel,
            pareto_frontier: ParetoFrontier,
            logger=None
    ):
        assert designer_config in experiment_designer_config_store.parameter_space

        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.config: Point = designer_config
        self.optimization_problem: OptimizationProblem = optimization_problem
        self.pareto_frontier = pareto_frontier
        self.surrogate_model: MultiObjectiveRegressionModel = surrogate_model
        self.rng = np.random.Generator(np.random.PCG64())

        if designer_config.utility_function_implementation == ConfidenceBoundUtilityFunction.__name__:
            self.utility_function = ConfidenceBoundUtilityFunction(
                function_config=self.config.confidence_bound_utility_function_config,
                surrogate_model=self.surrogate_model,
                minimize=self.optimization_problem.objectives[0].minimize,
                logger=self.logger
            )

        elif designer_config.utility_function_implementation == MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__:
            assert self.pareto_frontier is not None
            self.utility_function = MultiObjectiveProbabilityOfImprovementUtilityFunction(
                function_config=self.config.multi_objective_probability_of_improvement_config,
                pareto_frontier=pareto_frontier,
                surrogate_model=self.surrogate_model,
                logger=self.logger
            )
        else:
            assert False

        numeric_optimizer_config = None
        if self.config.numeric_optimizer_implementation == RandomSearchOptimizer.__name__:
            numeric_optimizer_config = self.config.random_search_optimizer_config
        elif self.config.numeric_optimizer_implementation == GlowWormSwarmOptimizer.__name__:
            numeric_optimizer_config = self.config.glow_worm_swarm_optimizer_config
        elif self.config.numeric_optimizer_implementation == RandomNearIncumbentOptimizer.__name__:
            numeric_optimizer_config = self.config.random_near_incumbent_optimizer_config
        else:
            raise NotImplementedError(f"Unknown numeric optimizer implementation: {self.config.numeric_optimizer_config}")

        self.numeric_optimizer = UtilityFunctionOtimizerFactory.create_utility_function_optimizer(
            utility_function=self.utility_function,
            optimizer_type_name=self.config.numeric_optimizer_implementation,
            optimizer_config=numeric_optimizer_config,
            optimization_problem=self.optimization_problem,
            pareto_frontier=self.pareto_frontier,
            logger=self.logger
        )

    def suggest(self, context_values_dataframe=None, random=False):
        self.logger.debug(f"Suggest(random={random})")
        random_number = self.rng.random()
        override_random = random_number < self.config.fraction_random_suggestions
        random = random or override_random
        if random:
            suggestion = self.optimization_problem.parameter_space.random()
            self.logger.info(f"Producing random suggestion: {suggestion}")
            return suggestion
        try:
            suggestion = self.numeric_optimizer.suggest(context_values_dataframe)
            self.logger.info(f"Produced a guided suggestion: {suggestion}")
            return suggestion
        except UnableToProduceGuidedSuggestionException:
            self.logger.info(f"Failed to produce guided suggestion. Producing random suggestion instead.")
            return self.optimization_problem.parameter_space.random()

