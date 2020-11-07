#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import os
import random
import unittest

import numpy as np
import pandas as pd

from mlos.Logger import create_logger
from mlos.Tracer import Tracer

from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.Optimizers.BayesianOptimizer import BayesianOptimizer, bayesian_optimizer_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.GlowWormSwarmOptimizer import GlowWormSwarmOptimizer
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Optimizers.OptimumDefinition import OptimumDefinition
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Spaces import SimpleHypergrid, ContinuousDimension


import mlos.global_values as global_values

class TestBayesianOptimizer(unittest.TestCase):
    """ Tests if the random search optimizer can work with a lot of random configs and a ton of samples.

    """

    @classmethod
    def setUpClass(cls):
        """ Set's up all the objects needed to test the RandomSearchOptimizer

        To test the RandomSearchOptimizer we need to first construct:
        * an optimization problem
        * a utility function

        To construct a utility function we need the same set up as in the TestConfidenceBoundUtilityFunction
        test.


        :return:
        """

        cls.temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(cls.temp_dir):
            os.mkdir(cls.temp_dir)

        global_values.declare_singletons()
        global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)
        cls.logger = create_logger(logger_name=cls.__name__)

    @classmethod
    def tearDownClass(cls) -> None:
        trace_output_path = os.path.join(cls.temp_dir, "OptimizerTestTrace.json")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)


    def test_bayesian_optimizer_on_simple_2d_quadratic_function_pre_heated(self):
        """ Tests the bayesian optimizer on a simple quadratic function first feeding the optimizer a lot of data.

        """

        objective_function_config = objective_function_config_store.get_config_by_name('2d_quadratic_concave_up')
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config)
        random_params_df = objective_function.parameter_space.random_dataframe(num_samples=10000)

        y_df = objective_function.evaluate_dataframe(random_params_df)


        optimization_problem = OptimizationProblem(
            parameter_space=objective_function.parameter_space,
            objective_space=objective_function.output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        bayesian_optimizer = BayesianOptimizer(
            optimization_problem=optimization_problem,
            optimizer_config=bayesian_optimizer_config_store.default,
            logger=self.logger
        )
        bayesian_optimizer.register(random_params_df, y_df)

        num_guided_samples = 20
        for i in range(num_guided_samples):
            # Suggest the parameters
            suggested_params = bayesian_optimizer.suggest()
            target_value = objective_function.evaluate_point(suggested_params)

            self.logger.info(f"[{i}/{num_guided_samples}] suggested params: {suggested_params}, target: {target_value}")

            # Register the observation with the optimizer
            bayesian_optimizer.register(suggested_params.to_dataframe(), target_value.to_dataframe())

        self.validate_optima(bayesian_optimizer)
        best_config_point, best_objective = bayesian_optimizer.optimum()
        self.logger.info(f"Optimum: {best_objective} Best Configuration: {best_config_point}")
        trace_output_path = os.path.join(self.temp_dir, "PreHeatedTrace.json")
        self.logger.info(f"Writing trace to {trace_output_path}")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)
        global_values.tracer.clear_events()

    def test_bayesian_optimizer_on_simple_2d_quadratic_function_cold_start(self):
        """ Tests the bayesian optimizer on a simple quadratic function with no prior data.

        """
        objective_function_config = objective_function_config_store.get_config_by_name('2d_quadratic_concave_up')
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config)

        optimization_problem = OptimizationProblem(
            parameter_space=objective_function.parameter_space,
            objective_space=objective_function.output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        bayesian_optimizer = BayesianOptimizer(
            optimization_problem=optimization_problem,
            optimizer_config=bayesian_optimizer_config_store.default,
            logger=self.logger
        )

        num_guided_samples = 1000
        for i in range(num_guided_samples):
            suggested_params = bayesian_optimizer.suggest()
            target_value = objective_function.evaluate_point(suggested_params)
            self.logger.info(f"[{i}/{num_guided_samples}] suggested params: {suggested_params}, target: {target_value}")


            bayesian_optimizer.register(suggested_params.to_dataframe(), target_value.to_dataframe())
            if i > 20 and i % 20 == 0:
                best_config_point, best_objective = bayesian_optimizer.optimum()
                self.logger.info(f"[{i}/{num_guided_samples}] Optimum config: {best_config_point}, optimum objective: {best_objective}")

        self.validate_optima(bayesian_optimizer)
        best_config, optimum = bayesian_optimizer.optimum()
        assert objective_function.parameter_space.contains_point(best_config)
        assert objective_function.output_space.contains_point(optimum)
        _, all_targets = bayesian_optimizer.get_all_observations()
        assert optimum.y == all_targets.min()[0]
        self.logger.info(f"Optimum: {optimum} best configuration: {best_config}")


    def test_hierarchical_quadratic_cold_start(self):

        objective_function_config = objective_function_config_store.get_config_by_name('three_level_quadratic')
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=objective_function.parameter_space,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        num_restarts = 1000
        for restart_num in range(num_restarts):
            bayesian_optimizer = BayesianOptimizer(
                optimization_problem=optimization_problem,
                optimizer_config=bayesian_optimizer_config_store.default,
                logger=self.logger
            )

            num_guided_samples = 200
            for i in range(num_guided_samples):
                suggested_params = bayesian_optimizer.suggest()
                y = objective_function.evaluate_point(suggested_params)
                self.logger.info(f"[{i}/{num_guided_samples}] {suggested_params}, y: {y}")

                input_values_df = suggested_params.to_dataframe()
                target_values_df = y.to_dataframe()
                bayesian_optimizer.register(input_values_df, target_values_df)
            self.validate_optima(bayesian_optimizer)
            best_config_point, best_objective = bayesian_optimizer.optimum()
            self.logger.info(f"[{restart_num}/{num_restarts}] Optimum config: {best_config_point}, optimum objective: {best_objective}")

    def test_hierarchical_quadratic_cold_start_random_configs(self):

        objective_function_config = objective_function_config_store.get_config_by_name('three_level_quadratic')
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=objective_function.parameter_space,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        random_state = random.Random()
        num_restarts = 200
        for restart_num in range(num_restarts):

            # Let's set up random seeds so that we can easily repeat failed experiments
            #
            random_state.seed(restart_num)
            bayesian_optimizer_config_store.parameter_space.random_state = random_state
            objective_function.parameter_space.random_state = random_state

            optimizer_config = bayesian_optimizer_config_store.parameter_space.random()

            # The goal here is to make sure the optimizer works with a lot of different configurations.
            # So let's make sure each run is not too long.
            #
            optimizer_config.min_samples_required_for_guided_design_of_experiments = 50
            if optimizer_config.surrogate_model_implementation == HomogeneousRandomForestRegressionModel.__name__:
                random_forest_config = optimizer_config.homogeneous_random_forest_regression_model_config
                random_forest_config.n_estimators = min(random_forest_config.n_estimators, 5)
                decision_tree_config = random_forest_config.decision_tree_regression_model_config
                decision_tree_config.min_samples_to_fit = 10
                decision_tree_config.n_new_samples_before_refit = 10

            if optimizer_config.experiment_designer_config.numeric_optimizer_implementation == GlowWormSwarmOptimizer.__name__:
                optimizer_config.experiment_designer_config.glow_worm_swarm_optimizer_config.num_iterations = 5


            self.logger.info(f"[Restart: {restart_num}/{num_restarts}] Creating a BayesianOptimimizer with the following config: ")
            self.logger.info(f"Optimizer config: {optimizer_config.to_json(indent=2)}")
            bayesian_optimizer = BayesianOptimizer(
                optimization_problem=optimization_problem,
                optimizer_config=optimizer_config,
                logger=self.logger
            )

            num_guided_samples = optimizer_config.min_samples_required_for_guided_design_of_experiments + 50
            for i in range(num_guided_samples):
                suggested_params = bayesian_optimizer.suggest()
                y = objective_function.evaluate_point(suggested_params)
                self.logger.info(f"[Restart: {restart_num}/{num_restarts}][Sample: {i}/{num_guided_samples}] {suggested_params}, y: {y}")

                input_values_df = suggested_params.to_dataframe()
                target_values_df = y.to_dataframe()
                bayesian_optimizer.register(input_values_df, target_values_df)

            best_config_point, best_objective = bayesian_optimizer.optimum()
            self.logger.info(f"[Restart: {restart_num}/{num_restarts}] Optimum config: {best_config_point}, optimum objective: {best_objective}")

    # pylint: disable=no-self-use
    def test_bayesian_optimizer_1d_nonconvex(self):
        # print seed for reproducible tests
        seed = np.random.randint(1e6)
        print(seed)
        random.seed(seed)
        np.random.seed(seed)
        sign = 1
        for minimize in [True, False]:
            # define function
            sign = 1 if minimize else -1
            def f(x):
                return (6*x-2)**2*np.sin(12*x-4)

            # setup hypergrid
            # single continuous input dimension between 0 and 1
            input_space = SimpleHypergrid(name="input", dimensions=[ContinuousDimension(name="x", min=0, max=1)])
            # define output space, we might not know the exact ranges
            output_space = SimpleHypergrid(name="objective",
                                           dimensions=[ContinuousDimension(name="function_value", min=-10, max=10)])

            optimization_problem = OptimizationProblem(
                parameter_space=input_space,
                objective_space=output_space,
                # we want to minimize the function
                objectives=[Objective(name="function_value", minimize=minimize)]
            )

            optimizer_config = bayesian_optimizer_config_store.default
            random_forest_config = optimizer_config.homogeneous_random_forest_regression_model_config

            random_forest_config.decision_tree_regression_model_config.n_new_samples_before_refit = 1

            random_forest_config.n_estimators = 20

            optimizer_config.experiment_designer_config.confidence_bound_utility_function_config.alpha = 0.1


            optimizer = BayesianOptimizer(optimization_problem, optimizer_config)

            def run_optimization(optimizer):
                # suggest new value from optimizer
                suggested_value = optimizer.suggest()
                input_values_df = suggested_value.to_dataframe()
                # suggested value are dictionary-like, keys are input space parameter names
                # evaluate target function
                target_value = sign * f(suggested_value['x'])

                # build dataframes to
                target_values_df = pd.DataFrame({'function_value': [target_value]})

                optimizer.register(input_values_df, target_values_df)

            for _ in range(40):
                run_optimization(optimizer)
            best_config_point, best_objective = optimizer.optimum()
            print(f"Optimum config: {best_config_point}, optimum objective: {best_objective}")
            self.assertLessEqual(sign * best_objective['function_value'], -5.5)

    def validate_optima(self, optimizer):
        if not optimizer.trained:
            # Computing prediction based optima should fail if the surrogate model is not trained.
            #
            with self.assertRaises(ValueError):
                optimizer.optimum(OptimumDefinition.PREDICTED_VALUE_FOR_OBSERVED_CONFIG)

            with self.assertRaises(ValueError):
                optimizer.optimum(OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG)

            with self.assertRaises(ValueError):
                optimizer.optimum(OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG)
        else:
            predicted_best_config, predicted_optimum = optimizer.optimum(OptimumDefinition.PREDICTED_VALUE_FOR_OBSERVED_CONFIG)
            ucb_90_ci_config, ucb_90_ci_optimum = optimizer.optimum(OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.1)
            ucb_95_ci_config, ucb_95_ci_optimum = optimizer.optimum(OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.05)
            ucb_99_ci_config, ucb_99_ci_optimum = optimizer.optimum(OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.01)

            lcb_90_ci_config, lcb_90_ci_optimum = optimizer.optimum(OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.1)
            lcb_95_ci_config, lcb_95_ci_optimum = optimizer.optimum(OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.05)
            lcb_99_ci_config, lcb_99_ci_optimum = optimizer.optimum(OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.01)

            # At the very least we can assert the ordering. Note that the configs corresponding to each of the below confidence bounds can be different, as confidence intervals
            # change width non-linearily both with degrees of freedom, and with prediction variance.
            #
            assert lcb_99_ci_optimum.lower_confidence_bound <= lcb_95_ci_optimum.lower_confidence_bound <= lcb_90_ci_optimum.lower_confidence_bound <= predicted_optimum.predicted_value
            assert predicted_optimum.predicted_value <= ucb_90_ci_optimum.upper_confidence_bound <= ucb_95_ci_optimum.upper_confidence_bound <= ucb_99_ci_optimum.upper_confidence_bound

