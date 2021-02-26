#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.UtilityFunction import UtilityFunction
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.GlowWormSwarmOptimizer import GlowWormSwarmOptimizer, glow_worm_swarm_optimizer_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.RandomNearIncumbentOptimizer import RandomNearIncumbentOptimizer, random_near_incumbent_optimizer_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.RandomSearchOptimizer import RandomSearchOptimizer, random_search_optimizer_config_store
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Spaces import Point

class UtilityFunctionOtimizerFactory:
    """Creates specialized instances of the abstract base calss UtilityFunctionOptimzier."""

    @classmethod
    def create_utility_function_optimizer(
            cls,
            utility_function: UtilityFunction,
            optimizer_type_name: str,
            optimizer_config: Point,
            optimization_problem: OptimizationProblem,
            pareto_frontier: ParetoFrontier=None,
            logger=None
    ):
        if optimizer_type_name == RandomSearchOptimizer.__name__:
            assert optimizer_config in random_search_optimizer_config_store.parameter_space
            return RandomSearchOptimizer(
                optimizer_config=optimizer_config,
                optimization_problem=optimization_problem,
                utility_function=utility_function,
                logger=logger
            )

        if optimizer_type_name == GlowWormSwarmOptimizer.__name__:
            assert optimizer_config in glow_worm_swarm_optimizer_config_store.parameter_space
            return GlowWormSwarmOptimizer(
                optimizer_config=optimizer_config,
                optimization_problem=optimization_problem,
                utility_function=utility_function,
                logger=logger
            )

        if optimizer_type_name == RandomNearIncumbentOptimizer.__name__:
            assert optimizer_config in random_near_incumbent_optimizer_config_store.parameter_space
            assert pareto_frontier is not None
            return RandomNearIncumbentOptimizer(
                optimizer_config=optimizer_config,
                optimization_problem=optimization_problem,
                utility_function=utility_function,
                pareto_frontier=pareto_frontier,
                logger=logger
            )

        raise RuntimeError(f"Unsupported UtilityFunctionOptimizerType: {optimizer_type_name}")
