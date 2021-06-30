#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import Dict
from uuid import uuid4
import collections

import numpy as np
import pandas as pd
from mlos.Exceptions import UnableToProduceGuidedSuggestionException
from mlos.Logger import create_logger
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore
from mlos.Tracer import trace

from .UtilityFunctionOptimizers.GlowWormSwarmOptimizer import GlowWormSwarmOptimizer, \
    glow_worm_swarm_optimizer_config_store
from .UtilityFunctionOptimizers.RandomNearIncumbentOptimizer import RandomNearIncumbentOptimizer, \
    random_near_incumbent_optimizer_config_store
from .UtilityFunctionOptimizers.RandomSearchOptimizer import RandomSearchOptimizer, random_search_optimizer_config_store
from .UtilityFunctionOptimizers.UtilityFunctionOptimizerFactory import UtilityFunctionOptimizerFactory
from .UtilityFunctions.MultiObjectiveProbabilityOfImprovementUtilityFunction import \
    MultiObjectiveProbabilityOfImprovementUtilityFunction, \
    multi_objective_probability_of_improvement_utility_function_config_store

parallel_experiment_designer_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name='parallel_experiment_designer_config',
        dimensions=[
            CategoricalDimension('utility_function_implementation', values=[
                MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__
            ]),
            CategoricalDimension('numeric_optimizer_implementation', values=[
                RandomSearchOptimizer.__name__,
                GlowWormSwarmOptimizer.__name__
            ]),
            ContinuousDimension('fraction_random_suggestions', min=0, max=1),
            DiscreteDimension(name="max_pending_suggestions", min=0, max=10 ** 3),
        ]
    ).join(
        subgrid=multi_objective_probability_of_improvement_utility_function_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('utility_function_implementation',
                                                   values=[MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__])
    ).join(
        subgrid=random_search_optimizer_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('numeric_optimizer_implementation', values=[RandomSearchOptimizer.__name__])
    ).join(
        subgrid=glow_worm_swarm_optimizer_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('numeric_optimizer_implementation', values=[GlowWormSwarmOptimizer.__name__])
    ).join(
        subgrid=random_near_incumbent_optimizer_config_store.parameter_space,
        on_external_dimension=CategoricalDimension('numeric_optimizer_implementation',
                                                   values=[RandomNearIncumbentOptimizer.__name__])
    ),
    default=Point(
        utility_function_implementation=MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__,
        numeric_optimizer_implementation=RandomSearchOptimizer.__name__,
        multi_objective_probability_of_improvement_config=multi_objective_probability_of_improvement_utility_function_config_store.default,
        random_search_optimizer_config=random_search_optimizer_config_store.default,
        fraction_random_suggestions=0.5,
        max_pending_suggestions=20,
    )
)


class ParallelExperimentDesigner:
    """An experiment designer able to take advantage of experimentation platform's parallelism.

    This designer keeps track of outstanding suggestions (suggestions that the experimenter committed to trying) and for each such
    suggestion it assumes that its result will dominate the pareto frontier within the predictive distribution. It then adds
    that presumed result to our 'tentative_pareto_frontier' and keeps it there until the true result comes back from the experimenter.

    The utility function now operates on this 'tentative_pareto_frontier' scoring new suggestions against it.

    The idea is that we presume that our outstanding suggestions will push a small section of the pareto frontier outwards, and we
    make it less attractive to try new suggestions likely to advance the same section of the pareto frontier. Ideally, the optimizer
    will be able to suggest parameters advancing a different section of the pareto frontier.

    This is a really simple and computationally cheap way of leveraging experimenter's parallelism. We can use it as a baseline
    for more sophisticated approaches later.
    """

    def __init__(
        self,
        designer_config: Point,
        optimization_problem: OptimizationProblem,
        surrogate_model: MultiObjectiveRegressionModel,
        pareto_frontier: ParetoFrontier,
        logger=None
    ):
        assert designer_config in parallel_experiment_designer_config_store.parameter_space

        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.config: Point = designer_config
        self.optimization_problem: OptimizationProblem = optimization_problem
        self.pareto_frontier = pareto_frontier

        # This pareto frontier contains true pareto along with all speculative objectives for the pending suggestions.
        #
        self._tentative_pareto_frontier = ParetoFrontier(optimization_problem=optimization_problem, objectives_df=pareto_frontier.pareto_df)

        self.surrogate_model: MultiObjectiveRegressionModel = surrogate_model
        self.rng = np.random.Generator(np.random.PCG64())

        if designer_config.utility_function_implementation == MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__:
            assert self.pareto_frontier is not None
            self.utility_function = MultiObjectiveProbabilityOfImprovementUtilityFunction(
                function_config=self.config.multi_objective_probability_of_improvement_config,
                pareto_frontier=self._tentative_pareto_frontier,
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

        self.numeric_optimizer = UtilityFunctionOptimizerFactory.create_utility_function_optimizer(
            utility_function=self.utility_function,
            optimizer_type_name=self.config.numeric_optimizer_implementation,
            optimizer_config=numeric_optimizer_config,
            optimization_problem=self.optimization_problem,
            logger=self.logger
        )

        # We need to keep track of all pending suggestions.
        #
        self._pending_suggestions: collections.OrderedDict[str, Point] = collections.OrderedDict()

    @trace()
    def suggest(
        self,
        context_values_dataframe: pd.DataFrame = None,
        random: bool = False
    ):
        self.logger.debug(f"Suggest(random={random})")

        random_number = self.rng.random()
        override_random = random_number < self.config.fraction_random_suggestions
        random = random or override_random

        if random:
            suggestion = self.optimization_problem.parameter_space.random()
            self.logger.info(f"Producing random suggestion: {suggestion}")
        else:
            try:
                suggestion = self.numeric_optimizer.suggest(context_values_dataframe)
                self.logger.info(f"Produced a guided suggestion: {suggestion}")
                return suggestion
            except UnableToProduceGuidedSuggestionException:
                self.logger.info("Failed to produce guided suggestion. Producing random suggestion instead.")
                suggestion = self.optimization_problem.parameter_space.random()
                random = True

        # Need to assign an id to each of the suggestions so that we know what's up. It's a little hack for now, we can explore
        # how to productize it later.
        #
        suggestion['__mlos_metadata'] = Point(
            suggestion_id=str(uuid4()),
            random=random
        )

        self.add_pending_suggestion(suggestion)

        return suggestion

    @trace()
    def add_pending_suggestion(
        self,
        suggestion: Point
    ):
        """Adds a pending suggestion to our internal data structures.

        The experimenter has committed to testing a given suggestion so we can add it and its predictions to our tentative
        pareto frontier. This is a resource management problem. If the experimenter never gives us back the result, we will
        have effectively leaked this pending suggestion and actually prevented the optimizer from exploring its neighborhoods
        in the future. So the experimenter must remember to either register a relevant observation, or drop a pending suggestion.

        :param suggestion:
        :return:
        """
        suggestion_id = suggestion["__mlos_metadata.suggestion_id"]

        # Keep number pending suggestions in limits.
        #
        num_pending_suggestions = len(self._pending_suggestions)
        max_pending_suggestions = self.config.max_pending_suggestions

        if num_pending_suggestions > max_pending_suggestions:
            # Remove pending suggestions in the order they were created.
            #
            self._pending_suggestions.popitem(last=False)

        self._pending_suggestions[suggestion_id] = suggestion
        self._update_tentative_pareto()

    def remove_pending_suggestion(
        self,
        suggestion: Point,
        update_tentative_pareto: bool = True
    ):
        if "__mlos_metadata.suggestion_id" in suggestion:
            suggestion_id = suggestion["__mlos_metadata.suggestion_id"]
            if suggestion_id in self._pending_suggestions:
                del self._pending_suggestions[suggestion_id]

        if update_tentative_pareto:
            self._update_tentative_pareto()

    def remove_pending_suggestions(
        self,
        suggestions_df: pd.DataFrame
    ):
        for row_idx, row in suggestions_df.iterrows():
            suggestion = Point.from_dataframe(row.to_frame().T)
            self.remove_pending_suggestion(suggestion, update_tentative_pareto=False)

        self._update_tentative_pareto()

    @trace()
    def _update_tentative_pareto(self):
        """Updates the tentative pareto frontier to include monte carlo samples from the pending suggestions."""

        num_pending_suggestions = len(self._pending_suggestions)
        all_objectives_dfs = []

        if num_pending_suggestions > 0:
            features_dfs = []
            for _, suggestion in self._pending_suggestions.items():
                parameters_df = suggestion.to_dataframe()
                features_df = self.optimization_problem.construct_feature_dataframe(parameters_df=parameters_df)
                features_dfs.append(features_df)

            features_for_all_pending_suggestions_df = pd.concat(features_dfs, ignore_index=True)
            all_predictions = self.surrogate_model.predict(features_df=features_for_all_pending_suggestions_df, )

            for i in range(num_pending_suggestions):
                monte_carlo_objectives_df = all_predictions.create_monte_carlo_samples_df(row_idx=i, num_samples=100, max_t_statistic=1)
                all_objectives_dfs.append(monte_carlo_objectives_df)

        all_objectives_dfs.append(self.pareto_frontier.pareto_df)
        empirical_and_speculative_objectives_df = pd.concat(all_objectives_dfs)
        self._tentative_pareto_frontier.update_pareto(objectives_df=empirical_and_speculative_objectives_df)
