#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import os
import pytest

import mlos.global_values as global_values
from mlos.Exceptions import UnableToProduceGuidedSuggestionException
from mlos.Logger import create_logger

from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.RandomSearchOptimizer import RandomSearchOptimizer, random_search_optimizer_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.RandomNearIncumbentOptimizer import RandomNearIncumbentOptimizer, random_near_incumbent_optimizer_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.GlowWormSwarmOptimizer import GlowWormSwarmOptimizer, glow_worm_swarm_optimizer_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.unit_tests.MultiObjectivePassThroughModelForTesting import MultiObjectivePassThroughModelForTesting, multi_objective_pass_through_model_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.UtilityFunctionOtimizerFactory import UtilityFunctionOtimizerFactory
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.ConfidenceBoundUtilityFunction import ConfidenceBoundUtilityFunction
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.MultiObjectiveProbabilityOfImprovementUtilityFunction import MultiObjectiveProbabilityOfImprovementUtilityFunction, multi_objective_probability_of_improvement_utility_function_config_store
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Optimizers.RegressionModels.MultiObjectiveHomogeneousRandomForest import MultiObjectiveHomogeneousRandomForest, homogeneous_random_forest_config_store
from mlos.Spaces import Point
from mlos.Tracer import Tracer, trace


class TestUtilityFunctionOptimizers:
    """ Tests if the utility function optimizers do anything useful at all.

    """

    @classmethod
    def setup_class(cls):
        """ Set's up all the objects needed to test the UtilityFunctionOptimizers

        To test the UtilityFunctionOptimizers we need to first construct:
            * an objective function for the model to approximate and its corresponding parameter and output spaces
            * an optimization problem
            * a regression model, then train it on some random parameters to the objective function
            * a utility function that utilizes the model
            * a pareto frontier over the random parameters

            And only then do we get to test our utility function optimizers. This is a lot of work and a somewhat cleaner approach
        would be to simply create an instance of the BayesianOptimizer to do all of the above for us, but then we might not be able
        to test the utility function optimizers as thoroughly as we need to.



        :return:
        """
        global_values.declare_singletons()
        global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)

        cls.logger = create_logger("TestUtilityFunctionOptimizers")

        cls.model_config = multi_objective_pass_through_model_config_store.default

        cls.model = MultiObjectivePassThroughModelForTesting(
            model_config=cls.model_config,
            logger=cls.logger
        )
        cls.objective_function = cls.model.objective_function
        cls.parameter_space = cls.objective_function.parameter_space
        cls.objective_space = cls.objective_function.output_space

        cls.optimization_problem = cls.objective_function.default_optimization_problem
        cls.utility_function_config = Point(utility_function_name="upper_confidence_bound_on_improvement", alpha=0.05)

        cls.utility_function = ConfidenceBoundUtilityFunction(
            function_config=cls.utility_function_config,
            surrogate_model=cls.model,
            minimize=cls.optimization_problem.objectives[0].minimize,
            logger=cls.logger
        )

        # To make the pareto frontier we have to generate some random points.
        #
        cls.parameters_df = cls.objective_function.parameter_space.random_dataframe(1000)
        cls.objectives_df = cls.objective_function.evaluate_dataframe(cls.parameters_df)

        cls.pareto_frontier = ParetoFrontier(
            optimization_problem=cls.optimization_problem,
            objectives_df=cls.objectives_df,
            parameters_df=cls.parameters_df
        )

    @classmethod
    def teardown_class(cls) -> None:
        temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
        trace_output_path = os.path.join(temp_dir, "TestUtilityFunctionOptimizers.json")
        print(f"Dumping trace to {trace_output_path}")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    @trace()
    def test_random_search_optimizer(self):
        print("##############################################")
        random_search_optimizer = RandomSearchOptimizer(
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            optimizer_config=random_search_optimizer_config_store.default,
            logger=self.logger
        )
        for _ in range(5):
            suggested_params = random_search_optimizer.suggest()
            print(suggested_params.to_json())
            assert suggested_params in self.parameter_space

    @trace()
    def test_glow_worm_swarm_optimizer(self):
        print("##############################################")
        glow_worm_swarm_optimizer = GlowWormSwarmOptimizer(
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            optimizer_config=glow_worm_swarm_optimizer_config_store.default,
            logger=self.logger
        )
        for _ in range(5):
            suggested_params = glow_worm_swarm_optimizer.suggest()
            print(suggested_params.to_json())
            assert suggested_params in self.parameter_space, f"{suggested_params.to_json(indent=2)} not in {self.parameter_space}"
            assert suggested_params in self.parameter_space

    @trace()
    def test_random_near_incumbent_optimizer(self):
        random_near_incumbent_optimizer = RandomNearIncumbentOptimizer(
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            optimizer_config=random_near_incumbent_optimizer_config_store.default,
            pareto_frontier=self.pareto_frontier,
            logger=self.logger
        )

        for _ in range(5):
            suggested_params = random_near_incumbent_optimizer.suggest()
            print(suggested_params.to_json(indent=2))
            assert suggested_params in self.parameter_space

    @trace()
    def test_glow_worm_on_three_level_quadratic(self):

        glow_worm_swarm_optimizer = GlowWormSwarmOptimizer(
            optimization_problem=self.optimization_problem,
            utility_function=self.utility_function,
            optimizer_config=glow_worm_swarm_optimizer_config_store.default
        )

        num_iterations = 5
        num_guided_suggestions = 0
        for i in range(num_iterations):
            try:
                suggested_params = glow_worm_swarm_optimizer.suggest()
                num_guided_suggestions += 1
                print(f"[{i+1}/{num_iterations}] {suggested_params.to_json()}")
                assert suggested_params in self.objective_function.parameter_space
            except UnableToProduceGuidedSuggestionException:
                self.logger.info("Failed to produce guided suggestion.", exc_info=True)

        assert num_guided_suggestions > 0

    @pytest.mark.parametrize('dummy_model_config_name', ['multi_objective_waves_3_params_2_objectives_half_pi_phase_difference', 'three_level_quadratic'])
    @pytest.mark.parametrize('utility_function_optimizer_type_name', [GlowWormSwarmOptimizer.__name__, RandomSearchOptimizer.__name__, RandomNearIncumbentOptimizer.__name__])
    @trace()
    def test_utility_function_optimizer_against_dummy_surrogate_model(self, dummy_model_config_name, utility_function_optimizer_type_name):

        dummy_model_config = multi_objective_pass_through_model_config_store.get_config_by_name(dummy_model_config_name)
        optimization_problem, model, utility_function, pareto_frontier = self._prepare_dummy_model_based_test_artifacts(dummy_model_config=dummy_model_config, logger=self.logger)

        if utility_function_optimizer_type_name == RandomSearchOptimizer.__name__:
            utility_function_optimizer_config = random_search_optimizer_config_store.default
        elif utility_function_optimizer_type_name == GlowWormSwarmOptimizer.__name__:
            utility_function_optimizer_config = glow_worm_swarm_optimizer_config_store.default
        elif utility_function_optimizer_type_name == RandomNearIncumbentOptimizer.__name__:
            utility_function_optimizer_config = random_near_incumbent_optimizer_config_store.default
        else:
            assert False, f"Unknown utility_function_optimizer_type_name: {utility_function_optimizer_type_name}"

        utility_function_optimizer = UtilityFunctionOtimizerFactory.create_utility_function_optimizer(
            utility_function=utility_function,
            optimizer_type_name=utility_function_optimizer_type_name,
            optimizer_config=utility_function_optimizer_config,
            optimization_problem=optimization_problem,
            pareto_frontier=pareto_frontier,
            logger=self.logger
        )

        for _ in range(3):
            suggested_params = utility_function_optimizer.suggest()
            objective_vaules = model.objective_function.evaluate_point(suggested_params)
            self.logger.info(suggested_params)
            self.logger.info(objective_vaules)
            assert suggested_params in optimization_problem.parameter_space

    @pytest.mark.parametrize('objective_function_config_name', ["three_level_quadratic", "multi_objective_waves_3_params_2_objectives_half_pi_phase_difference"])
    @pytest.mark.parametrize('utility_function_type_name', [ConfidenceBoundUtilityFunction.__name__, MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__])
    @pytest.mark.parametrize('utility_function_optimizer_type_name', [GlowWormSwarmOptimizer.__name__, RandomSearchOptimizer.__name__, RandomNearIncumbentOptimizer.__name__])
    @trace()
    def test_optimizers_against_untrained_models(self, objective_function_config_name, utility_function_type_name, utility_function_optimizer_type_name):
        """Tests that the utility function optimizers throw appropriate exceptions when the utility function cannot be evaluated.

        :return:
        """
        self.logger.info(f"Creating test artifacts for objective function: {objective_function_config_name}, utility_function: {utility_function_optimizer_type_name}, optimizer: {utility_function_optimizer_type_name}.")
        model_config = homogeneous_random_forest_config_store.default
        objective_function_config = objective_function_config_store.get_config_by_name(objective_function_config_name)
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)
        optimization_problem = objective_function.default_optimization_problem

        model = MultiObjectiveHomogeneousRandomForest(
            model_config=model_config,
            input_space=optimization_problem.feature_space,
            output_space=optimization_problem.objective_space,
            logger=self.logger
        )
        pareto_frontier = ParetoFrontier(optimization_problem=optimization_problem)

        if utility_function_type_name == ConfidenceBoundUtilityFunction.__name__:
            utility_function_config = Point(utility_function_name="upper_confidence_bound_on_improvement", alpha=0.05)
            utility_function = ConfidenceBoundUtilityFunction(
                function_config=utility_function_config,
                surrogate_model=model,
                minimize=optimization_problem.objectives[0].minimize,
                logger=self.logger
            )
        elif utility_function_type_name == MultiObjectiveProbabilityOfImprovementUtilityFunction.__name__:
            utility_function_config = multi_objective_probability_of_improvement_utility_function_config_store.default
            utility_function = MultiObjectiveProbabilityOfImprovementUtilityFunction(
                function_config=utility_function_config,
                pareto_frontier=pareto_frontier,
                surrogate_model=model,
                logger=self.logger
            )
        else:
            assert False

        if utility_function_optimizer_type_name == RandomSearchOptimizer.__name__:
            utility_function_optimizer_config = random_search_optimizer_config_store.default
        elif utility_function_optimizer_type_name == GlowWormSwarmOptimizer.__name__:
            utility_function_optimizer_config = glow_worm_swarm_optimizer_config_store.default
        elif utility_function_optimizer_type_name == RandomNearIncumbentOptimizer.__name__:
            utility_function_optimizer_config = random_near_incumbent_optimizer_config_store.default
        else:
            assert False, f"Unknown utility_function_optimizer_type_name: {utility_function_optimizer_type_name}"

        utility_function_optimizer = UtilityFunctionOtimizerFactory.create_utility_function_optimizer(
            utility_function=utility_function,
            optimizer_type_name=utility_function_optimizer_type_name,
            optimizer_config=utility_function_optimizer_config,
            optimization_problem=optimization_problem,
            pareto_frontier=pareto_frontier,
            logger=self.logger
        )

        assert not model.trained

        self.logger.info("Asserting the optimizer is throwing appropriate exceptions.")
        num_failed_suggestions = 3
        for i in range(num_failed_suggestions):
            with pytest.raises(expected_exception=UnableToProduceGuidedSuggestionException):
                utility_function_optimizer.suggest()
            self.logger.info(f"[{i+1}/{num_failed_suggestions}] worked.")


        # Now let's train the model a bit and make sure that we can produce the suggestions afterwards
        #
        random_params_df = optimization_problem.parameter_space.random_dataframe(1000)
        objectives_df = objective_function.evaluate_dataframe(random_params_df)
        features_df = optimization_problem.construct_feature_dataframe(parameters_df=random_params_df)

        self.logger.info("Training the model")
        model.fit(features_df=features_df, targets_df=objectives_df, iteration_number=1000)
        assert model.trained
        self.logger.info("Model trained.")

        self.logger.info("Updating pareto.")
        pareto_frontier.update_pareto(objectives_df=objectives_df, parameters_df=random_params_df)
        self.logger.info("Pareto updated.")

        self.logger.info("Asserting suggestions work.")
        num_successful_suggestions = 3
        for i in range(num_successful_suggestions):
            suggestion = utility_function_optimizer.suggest()
            assert suggestion in optimization_problem.parameter_space
            self.logger.info(f"[{i+1}/{num_successful_suggestions}] successfully produced suggestion: {suggestion}")

        self.logger.info(f"Done testing. Objective function: {objective_function_config_name}, utility_function: {utility_function_optimizer_type_name}, optimizer: {utility_function_optimizer_type_name}.")

    def _prepare_dummy_model_based_test_artifacts(self, dummy_model_config, logger):
        """Prepares all the artifacts we need to create and run a utility function optimizer.

        I chose to create them here rather than in setup class, to avoid unnecessarily creating all possible combinations for all
        possible tests. It's easier and cheaper to produce this artifacts just in time, rather than upfront.

        I suspect that pytest has a functionality to accomplish just this, but haven't found it yet.

        We need to produce:
        * an optimization problem
        * a model
        * a utility function
        * pareto frontier
        """
        model = MultiObjectivePassThroughModelForTesting(model_config=dummy_model_config, logger=logger)
        objective_function = model.objective_function
        optimization_problem = objective_function.default_optimization_problem

        # Let's create the pareto frontier.
        #
        params_df = objective_function.parameter_space.random_dataframe(1000)
        objectives_df = objective_function.evaluate_dataframe(params_df)
        pareto_frontier = ParetoFrontier(
            optimization_problem=optimization_problem,
            objectives_df=objectives_df,
            parameters_df=params_df
        )

        if len(optimization_problem.objectives) == 1:
            utility_function_config = Point(utility_function_name="upper_confidence_bound_on_improvement", alpha=0.05)
            utility_function=ConfidenceBoundUtilityFunction(
                function_config=utility_function_config,
                surrogate_model=model,
                minimize=optimization_problem.objectives[0].minimize,
                logger=logger
            )
        else:
            utility_function_config = multi_objective_probability_of_improvement_utility_function_config_store.default
            utility_function = MultiObjectiveProbabilityOfImprovementUtilityFunction(
                function_config=utility_function_config,
                pareto_frontier=pareto_frontier,
                surrogate_model=model,
                logger=logger
            )
        return optimization_problem, model, utility_function, pareto_frontier
