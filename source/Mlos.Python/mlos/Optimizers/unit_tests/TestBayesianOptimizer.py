#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import os
import random
import unittest
import warnings

import numpy as np
import pandas as pd

from mlos.Logger import create_logger
from mlos.Tracer import Tracer

from mlos.Optimizers.BayesianOptimizer import BayesianOptimizer, BayesianOptimizerConfig
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType

from mlos.Spaces import SimpleHypergrid, ContinuousDimension

from mlos.SynthethicFunctions.sample_functions import quadratic
from mlos.SynthethicFunctions.HierarchicalFunctions import MultilevelQuadratic

import mlos.global_values as global_values


class TestBayesianOptimizer(unittest.TestCase):
    """ Tests if the random search optimizer does anything useful at all.

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
        warnings.simplefilter("error")
        cls.temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(cls.temp_dir):
            os.mkdir(cls.temp_dir)

        global_values.declare_singletons()
        global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)
        cls.logger = create_logger(logger_name=cls.__name__)

    @classmethod
    def tearDownClass(cls) -> None:
        trace_output_path = os.path.join(cls.temp_dir, "TestBayesianOptimizerTrace.json")
        print(f"Dumping trace to {trace_output_path}")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    def test_bayesian_optimizer_on_simple_2d_quadratic_function_pre_heated(self):
        """ Tests the bayesian optimizer on a simple quadratic function first feeding the optimizer a lot of data.

        :return:
        """
        input_space = SimpleHypergrid(
            name="input",
            dimensions=[
                ContinuousDimension(name='x_1', min=-100, max=100),
                ContinuousDimension(name='x_2', min=-100, max=100)
            ]
        )

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        x_1, x_2 = np.meshgrid(
            input_space['x_1'].linspace(num=101),
            input_space['x_2'].linspace(num=101)
        )

        y = quadratic(x_1=x_1, x_2=x_2)

        input_values_dataframe = pd.DataFrame({'x_1': x_1.reshape(-1), 'x_2': x_2.reshape(-1)})
        output_values_dataframe = pd.DataFrame({'y': y.reshape(-1)})

        optimization_problem = OptimizationProblem(
            parameter_space=input_space,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        bayesian_optimizer = BayesianOptimizer(
            optimization_problem=optimization_problem,
            optimizer_config=BayesianOptimizerConfig.DEFAULT,
            logger=self.logger
        )
        bayesian_optimizer.register(input_values_dataframe, output_values_dataframe)

        num_guided_samples = 2
        for _ in range(num_guided_samples):
            # Suggest the parameters
            suggested_params = bayesian_optimizer.suggest()
            suggested_params_dict = suggested_params.to_dict()

            # Reformat them to feed the parameters to the target
            target_value = quadratic(**suggested_params_dict)
            print(suggested_params, target_value)

            # Reformat the observation to feed it back to the optimizer
            input_values_df = pd.DataFrame({param_name: [param_value] for param_name, param_value in suggested_params_dict.items()})
            target_values_df = pd.DataFrame({'y': [target_value]})

            # Register the observation with the optimizer
            bayesian_optimizer.register(input_values_df, target_values_df)

        print(bayesian_optimizer.optimum()[1])

    def test_optimum_before_register_error(self):
        input_space = SimpleHypergrid(
            name="input",
            dimensions=[ContinuousDimension(name='x', min=-10, max=10)])

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[ContinuousDimension(name='y', min=-math.inf, max=math.inf)])
        optimization_problem = OptimizationProblem(
            parameter_space=input_space,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )
        bayesian_optimizer = BayesianOptimizer(
            optimization_problem=optimization_problem,
            logger=self.logger,
            optimizer_config=BayesianOptimizerConfig.DEFAULT
        )
        with self.assertRaises(ValueError):
            bayesian_optimizer.optimum()

        bayesian_optimizer.register(pd.DataFrame({'x': [0.]}), pd.DataFrame({'y': [1.]}))
        bayesian_optimizer.optimum()

    def test_bayesian_optimizer_on_simple_2d_quadratic_function_cold_start(self):
        """ Tests the bayesian optimizer on a simple quadratic function with no prior data.

        :return:
        """
        input_space = SimpleHypergrid(
            name="input",
            dimensions=[
                ContinuousDimension(name='x_1', min=-10, max=10),
                ContinuousDimension(name='x_2', min=-10, max=10)
            ]
        )

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=input_space,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        optimizer_config = BayesianOptimizerConfig.DEFAULT
        optimizer_config.min_samples_required_for_guided_design_of_experiments = 50
        optimizer_config.homogeneous_random_forest_regression_model_config.n_estimators = 10
        optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.splitter = "best"
        optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.n_new_samples_before_refit = 2

        print(optimizer_config.to_json(indent=2))

        bayesian_optimizer = BayesianOptimizer(
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config,
            logger=self.logger
        )

        num_iterations = 62
        for i in range(num_iterations):
            suggested_params = bayesian_optimizer.suggest()
            suggested_params_dict = suggested_params.to_dict()
            target_value = quadratic(**suggested_params_dict)
            print(f"[{i+1}/{num_iterations}] Suggested params: {suggested_params_dict}, target_value: {target_value}")

            input_values_df = pd.DataFrame({param_name: [param_value] for param_name, param_value in suggested_params_dict.items()})
            target_values_df = pd.DataFrame({'y': [target_value]})

            bayesian_optimizer.register(input_values_df, target_values_df)
            if i > optimizer_config.min_samples_required_for_guided_design_of_experiments and i % 10 == 1:
                print(f"[{i}/{num_iterations}] Optimum: {bayesian_optimizer.optimum()[1]}")
                convergence_state = bayesian_optimizer.get_optimizer_convergence_state()
                random_forest_fit_state = convergence_state.surrogate_model_fit_state
                random_forest_gof_metrics = random_forest_fit_state.current_train_gof_metrics
                print(f"Relative squared error: {random_forest_gof_metrics.relative_squared_error}, Relative absolute error: {random_forest_gof_metrics.relative_absolute_error}")

        convergence_state = bayesian_optimizer.get_optimizer_convergence_state()
        random_forest_fit_state = convergence_state.surrogate_model_fit_state
        random_forest_gof_metrics = random_forest_fit_state.current_train_gof_metrics
        self.assertTrue(random_forest_gof_metrics.last_refit_iteration_number > 0.7 * num_iterations)
        models_gof_metrics = [random_forest_gof_metrics]
        for decision_tree_fit_state in random_forest_fit_state.decision_trees_fit_states:
            models_gof_metrics.append(decision_tree_fit_state.current_train_gof_metrics)

        for model_gof_metrics in models_gof_metrics:
            self.assertTrue(0 <= model_gof_metrics.relative_absolute_error <= 1)  # This could fail if the models are really wrong. Not expected in this unit test though.
            self.assertTrue(0 <= model_gof_metrics.relative_squared_error <= 1)

            # There is an invariant linking mean absolute error (MAE), root mean squared error (RMSE) and number of observations (n) let's assert it.
            n = model_gof_metrics.last_refit_iteration_number
            self.assertTrue(model_gof_metrics.mean_absolute_error <= model_gof_metrics.root_mean_squared_error <= math.sqrt(n) * model_gof_metrics.mean_absolute_error)

            # We know that the sample confidence interval is wider (or equal to) prediction interval. So hit rates should be ordered accordingly.
            self.assertTrue(model_gof_metrics.sample_90_ci_hit_rate >= model_gof_metrics.prediction_90_ci_hit_rate)

        goodness_of_fit_df = random_forest_fit_state.get_goodness_of_fit_dataframe(data_set_type=DataSetType.TRAIN)
        print(goodness_of_fit_df.head())

        goodness_of_fit_df = random_forest_fit_state.get_goodness_of_fit_dataframe(
            data_set_type=DataSetType.TRAIN,
            deep=True
        )
        print(goodness_of_fit_df.head())

    def test_hierarchical_quadratic_cold_start(self):

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=MultilevelQuadratic.CONFIG_SPACE,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        num_restarts = 2
        for restart_num in range(num_restarts):
            bayesian_optimizer = BayesianOptimizer(
                optimization_problem=optimization_problem,
                optimizer_config=BayesianOptimizerConfig.DEFAULT,
                logger=self.logger
            )

            num_guided_samples = 200
            for i in range(num_guided_samples):
                suggested_params = bayesian_optimizer.suggest()
                y = MultilevelQuadratic.evaluate(suggested_params)
                print(f"[{i}/{num_guided_samples}] {suggested_params}, y: {y}")

                input_values_df = pd.DataFrame({
                    param_name: [param_value]
                    for param_name, param_value in suggested_params
                })
                target_values_df = pd.DataFrame({'y': [y]})
                bayesian_optimizer.register(input_values_df, target_values_df)

            print(f"[{restart_num}/{num_restarts}] Optimum: {bayesian_optimizer.optimum()[1]}")


    def test_hierarchical_quadratic_cold_start_random_configs(self):

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=MultilevelQuadratic.CONFIG_SPACE,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        random_state = random.Random()
        num_restarts = 1
        has_failed = False
        for restart_num in range(num_restarts):
            try:
                # Let's set up random seeds so that we can easily repeat failed experiments
                #
                random_state.seed(restart_num)
                BayesianOptimizerConfig.CONFIG_SPACE.random_state = random_state
                MultilevelQuadratic.CONFIG_SPACE.random_state = random_state

                optimizer_config = BayesianOptimizerConfig.CONFIG_SPACE.random()
                print(f"[Restart: {restart_num}/{num_restarts}] Creating a BayesianOptimimizer with the following config: ")
                print(optimizer_config.to_json(indent=2))
                bayesian_optimizer = BayesianOptimizer(
                    optimization_problem=optimization_problem,
                    optimizer_config=optimizer_config,
                    logger=self.logger
                )

                num_guided_samples = optimizer_config.min_samples_required_for_guided_design_of_experiments + 50
                for i in range(num_guided_samples):
                    suggested_params = bayesian_optimizer.suggest()
                    y = MultilevelQuadratic.evaluate(suggested_params)
                    print(f"[Restart: {restart_num}/{num_restarts}][Sample: {i}/{num_guided_samples}] {suggested_params}, y: {y}")

                    input_values_df = pd.DataFrame({
                        param_name: [param_value]
                        for param_name, param_value in suggested_params
                    })
                    target_values_df = pd.DataFrame({'y': [y]})
                    bayesian_optimizer.register(input_values_df, target_values_df)

                print(f"[Restart: {restart_num}/{num_restarts}] Optimum: {bayesian_optimizer.optimum()[1]}")
            except Exception as e:
                has_failed = True
                error_file_path = os.path.join(os.getcwd(), "temp", "test_errors.txt")
                with open(error_file_path, 'a') as out_file:
                    out_file.write(
                        "##################################################################################\n")
                    out_file.write(f"{restart_num} failed.\n")
                    out_file.write(f"Exception: {e}")
        self.assertFalse(has_failed)


    def test_bayesian_optimizer_default_copies_parameters(self):
        config = BayesianOptimizerConfig.DEFAULT
        config.min_samples_required_for_guided_design_of_experiments = 1
        config.experiment_designer_config.fraction_random_suggestions = .1

        original_config = BayesianOptimizerConfig.DEFAULT
        assert original_config.min_samples_required_for_guided_design_of_experiments == 10
        print(original_config.experiment_designer_config.fraction_random_suggestions)
        assert original_config.experiment_designer_config.fraction_random_suggestions == .5
