#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import os
import pickle
import random
import unittest
import warnings

import grpc
import numpy as np
import pandas as pd

from mlos.Logger import create_logger

import mlos.global_values as global_values
from mlos.Grpc.OptimizerMicroserviceServer import OptimizerMicroserviceServer
from mlos.OptimizerEvaluationTools.SyntheticFunctions.sample_functions import quadratic
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.Optimizers.BayesianOptimizerConfigStore import bayesian_optimizer_config_store
from mlos.Optimizers.BayesianOptimizerFactory import BayesianOptimizerFactory
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.GlowWormSwarmOptimizer import GlowWormSwarmOptimizer
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Optimizers.OptimizerBase import OptimizerBase
from mlos.Optimizers.OptimumDefinition import OptimumDefinition
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import SimpleHypergrid, ContinuousDimension
from mlos.Tracer import Tracer, trace, traced


class TestBayesianOptimizer(unittest.TestCase):
    """ Tests if the random search optimizer does anything useful at all.

    """

    @classmethod
    def setUpClass(cls):
        """ Sets up all the singletons needed to test the BayesianOptimizer.

        """
        warnings.simplefilter("error")
        global_values.declare_singletons()
        global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)
        cls.logger = create_logger(logger_name=cls.__name__)

        # Start up the gRPC service.
        #
        cls.server = OptimizerMicroserviceServer(port=50051, num_threads=10)
        cls.server.start()

        cls.optimizer_service_channel = grpc.insecure_channel('localhost:50051')
        cls.bayesian_optimizer_factory = BayesianOptimizerFactory(grpc_channel=cls.optimizer_service_channel, logger=cls.logger)


    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop(grace=None)

        cls.temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(cls.temp_dir):
            os.mkdir(cls.temp_dir)
        trace_output_path = os.path.join(cls.temp_dir, "TestBayesianOptimizerTrace.json")
        print(f"Dumping trace to {trace_output_path}")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    @trace()
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
            input_space['x_1'].linspace(num=21),
            input_space['x_2'].linspace(num=21)
        )

        y = quadratic(x_1=x_1, x_2=x_2)

        input_values_dataframe = pd.DataFrame({'x_1': x_1.reshape(-1), 'x_2': x_2.reshape(-1)})
        output_values_dataframe = pd.DataFrame({'y': y.reshape(-1)})

        optimization_problem = OptimizationProblem(
            parameter_space=input_space,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        local_optimizer = self.bayesian_optimizer_factory.create_local_optimizer(
            optimization_problem=optimization_problem,
            optimizer_config=bayesian_optimizer_config_store.default,
        )

        remote_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
            optimization_problem=optimization_problem,
            optimizer_config=bayesian_optimizer_config_store.default
        )

        optimizers = [local_optimizer, remote_optimizer]
        for bayesian_optimizer in optimizers:
            # A call to .optimum() should throw before we feed any data to the optimizer.
            #
            with self.assertRaises(ValueError):
                bayesian_optimizer.optimum(OptimumDefinition.BEST_OBSERVATION)
            self.validate_optima(optimizer=bayesian_optimizer)

            bayesian_optimizer.register(feature_values_pandas_frame=input_values_dataframe, target_values_pandas_frame=output_values_dataframe)
            observed_best_config, observed_best_optimum = bayesian_optimizer.optimum(OptimumDefinition.BEST_OBSERVATION)
            assert observed_best_optimum.y == output_values_dataframe['y'].min()

            self.validate_optima(optimizer=bayesian_optimizer)

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
                bayesian_optimizer.register(feature_values_pandas_frame=input_values_df, target_values_pandas_frame=target_values_df)

            best_config_point, best_objective = bayesian_optimizer.optimum()
            print(f"Optimum config: {best_config_point}, optimum objective: {best_objective}")

    @trace()
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
        bayesian_optimizer = self.bayesian_optimizer_factory.create_local_optimizer(
            optimization_problem=optimization_problem,
            optimizer_config=bayesian_optimizer_config_store.default
        )

        with self.assertRaises(ValueError):
            bayesian_optimizer.optimum()

        bayesian_optimizer.register(feature_values_pandas_frame=pd.DataFrame({'x': [0.]}), target_values_pandas_frame=pd.DataFrame({'y': [1.]}))
        bayesian_optimizer.optimum()

    @trace()
    def test_bayesian_optimizer_on_simple_2d_quadratic_function_cold_start(self):
        """Tests the bayesian optimizer on a simple quadratic function with no prior data.

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

        optimizer_config = bayesian_optimizer_config_store.default
        optimizer_config.min_samples_required_for_guided_design_of_experiments = 50
        optimizer_config.homogeneous_random_forest_regression_model_config.n_estimators = 10
        optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.splitter = "best"
        optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.n_new_samples_before_refit = 2

        print(optimizer_config.to_json(indent=2))

        local_optimizer = self.bayesian_optimizer_factory.create_local_optimizer(
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config
        )

        remote_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config
        )

        for bayesian_optimizer in [local_optimizer, remote_optimizer]:
            num_iterations = 62
            old_optimum = np.inf
            for i in range(num_iterations):
                suggested_params = bayesian_optimizer.suggest()
                suggested_params_dict = suggested_params.to_dict()
                target_value = quadratic(**suggested_params_dict)
                print(f"[{i+1}/{num_iterations}] Suggested params: {suggested_params_dict}, target_value: {target_value}")

                input_values_df = pd.DataFrame({param_name: [param_value] for param_name, param_value in suggested_params_dict.items()})
                target_values_df = pd.DataFrame({'y': [target_value]})

                bayesian_optimizer.register(feature_values_pandas_frame=input_values_df, target_values_pandas_frame=target_values_df)
                if i > optimizer_config.min_samples_required_for_guided_design_of_experiments and i % 10 == 1:
                    _, all_targets = bayesian_optimizer.get_all_observations()
                    best_config, optimum = bayesian_optimizer.optimum(optimum_definition=OptimumDefinition.BEST_OBSERVATION)
                    print(f"[{i}/{num_iterations}] Optimum: {optimum}")
                    assert optimum.y == all_targets.min()[0]
                    assert input_space.contains_point(best_config)
                    assert output_space.contains_point(optimum)
                    assert optimum.y <= old_optimum
                    old_optimum = optimum.y
                    self.validate_optima(optimizer=bayesian_optimizer)
                    random_forest_gof_metrics = bayesian_optimizer.compute_surrogate_model_goodness_of_fit()
                    print(f"Relative squared error: {random_forest_gof_metrics.relative_squared_error}, Relative absolute error: {random_forest_gof_metrics.relative_absolute_error}")

            random_forest_gof_metrics = bayesian_optimizer.compute_surrogate_model_goodness_of_fit()
            self.assertTrue(random_forest_gof_metrics.last_refit_iteration_number > 0.7 * num_iterations)
            models_gof_metrics = [random_forest_gof_metrics]

            for model_gof_metrics in models_gof_metrics:
                self.assertTrue(0 <= model_gof_metrics.relative_absolute_error <= 1)  # This could fail if the models are really wrong. Not expected in this unit test though.
                self.assertTrue(0 <= model_gof_metrics.relative_squared_error <= 1)

                # There is an invariant linking mean absolute error (MAE), root mean squared error (RMSE) and number of observations (n) let's assert it.
                n = model_gof_metrics.last_refit_iteration_number
                self.assertTrue(model_gof_metrics.mean_absolute_error <= model_gof_metrics.root_mean_squared_error <= math.sqrt(n) * model_gof_metrics.mean_absolute_error)

                # We know that the sample confidence interval is wider (or equal to) prediction interval. So hit rates should be ordered accordingly.
                self.assertTrue(model_gof_metrics.sample_90_ci_hit_rate >= model_gof_metrics.prediction_90_ci_hit_rate)

    @trace()
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

        num_restarts = 2
        for restart_num in range(num_restarts):

            optimizer_config = bayesian_optimizer_config_store.default
            optimizer_config.min_samples_required_for_guided_design_of_experiments = 20
            optimizer_config.homogeneous_random_forest_regression_model_config.n_estimators = 10
            optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.splitter = "best"
            optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.min_samples_to_fit = 10
            optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.n_new_samples_before_refit = 2

            local_optimizer = self.bayesian_optimizer_factory.create_local_optimizer(
                optimization_problem=optimization_problem,
                optimizer_config=optimizer_config
            )

            remote_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
                optimization_problem=optimization_problem,
                optimizer_config=optimizer_config
            )

            for bayesian_optimizer in [local_optimizer, remote_optimizer]:
                num_guided_samples = 50
                for i in range(num_guided_samples):
                    suggested_params = bayesian_optimizer.suggest()
                    y = objective_function.evaluate_point(suggested_params)
                    print(f"[{i}/{num_guided_samples}] {suggested_params}, y: {y}")

                    input_values_df = pd.DataFrame({
                        param_name: [param_value]
                        for param_name, param_value in suggested_params
                    })
                    target_values_df = y.to_dataframe()
                    bayesian_optimizer.register(feature_values_pandas_frame=input_values_df, target_values_pandas_frame=target_values_df)
                best_config_point, best_objective = bayesian_optimizer.optimum(optimum_definition=OptimumDefinition.BEST_OBSERVATION)
                print(f"[Restart:  {restart_num}/{num_restarts}] Optimum config: {best_config_point}, optimum objective: {best_objective}")
                self.validate_optima(optimizer=bayesian_optimizer)

    @trace()
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
        num_restarts = 10
        for restart_num in range(num_restarts):
            # Let's set up random seeds so that we can easily repeat failed experiments
            #
            random_state.seed(restart_num)
            bayesian_optimizer_config_store.parameter_space.random_state = random_state
            objective_function.parameter_space.random_state = random_state

            optimizer_config = bayesian_optimizer_config_store.parameter_space.random()

            # We can make this test more useful as a Unit Test by restricting its duration.
            #
            optimizer_config.min_samples_required_for_guided_design_of_experiments = 20
            if optimizer_config.surrogate_model_implementation == HomogeneousRandomForestRegressionModel.__name__:
                random_forest_config = optimizer_config.homogeneous_random_forest_regression_model_config
                random_forest_config.n_estimators = min(random_forest_config.n_estimators, 5)
                decision_tree_config = random_forest_config.decision_tree_regression_model_config
                decision_tree_config.min_samples_to_fit = 10
                decision_tree_config.n_new_samples_before_refit = 10

            if optimizer_config.experiment_designer_config.numeric_optimizer_implementation == GlowWormSwarmOptimizer.__name__:
                optimizer_config.experiment_designer_config.glow_worm_swarm_optimizer_config.num_iterations = 5

            print(f"[Restart: {restart_num}/{num_restarts}] Creating a BayesianOptimimizer with the following config: ")
            print(optimizer_config.to_json(indent=2))

            local_optimizer = self.bayesian_optimizer_factory.create_local_optimizer(
                optimization_problem=optimization_problem,
                optimizer_config=optimizer_config
            )

            remote_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
                optimization_problem=optimization_problem,
                optimizer_config=optimizer_config
            )

            for bayesian_optimizer in [local_optimizer, remote_optimizer]:
                num_guided_samples = optimizer_config.min_samples_required_for_guided_design_of_experiments + 10
                for i in range(num_guided_samples):
                    suggested_params = bayesian_optimizer.suggest()
                    y = objective_function.evaluate_point(suggested_params)
                    print(f"[Restart: {restart_num}/{num_restarts}][Sample: {i}/{num_guided_samples}] {suggested_params}, y: {y}")

                    input_values_df = pd.DataFrame({
                        param_name: [param_value]
                        for param_name, param_value in suggested_params
                    })
                    target_values_df = y.to_dataframe()
                    bayesian_optimizer.register(feature_values_pandas_frame=input_values_df,target_values_pandas_frame=target_values_df)

                best_config_point, best_objective = bayesian_optimizer.optimum(optimum_definition=OptimumDefinition.BEST_OBSERVATION)
                print(f"[Restart:  {restart_num}/{num_restarts}] Optimum config: {best_config_point}, optimum objective: {best_objective}")
                self.validate_optima(optimizer=bayesian_optimizer)

            # Test if pickling works
            #
            pickled_optimizer = pickle.dumps(local_optimizer)
            unpickled_optimizer = pickle.loads(pickled_optimizer)
            for _ in range(10):
                self.assertTrue(unpickled_optimizer.suggest() == local_optimizer.suggest())

    @trace()
    def test_bayesian_optimizer_default_copies_parameters(self):
        config = bayesian_optimizer_config_store.default
        config.min_samples_required_for_guided_design_of_experiments = 1
        config.experiment_designer_config.fraction_random_suggestions = .1

        original_config = bayesian_optimizer_config_store.default
        assert original_config.min_samples_required_for_guided_design_of_experiments == 10
        print(original_config.experiment_designer_config.fraction_random_suggestions)
        assert original_config.experiment_designer_config.fraction_random_suggestions == .5

    def validate_optima(self, optimizer: OptimizerBase):
        should_raise_for_predicted_value = False
        should_raise_for_confidence_bounds = False
        if not optimizer.trained:
            should_raise_for_predicted_value = True
            should_raise_for_confidence_bounds = True
        else:
            features_df, _ = optimizer.get_all_observations()
            predictions = optimizer.predict(feature_values_pandas_frame=features_df)
            predictions_df = predictions.get_dataframe()

            if len(predictions_df.index) == 0:
                should_raise_for_predicted_value = True
                should_raise_for_confidence_bounds = True

            # Drop nulls and zeroes.
            #
            predictions_df = predictions_df[
                predictions_df[Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value].notna() &
                (predictions_df[Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value] != 0)
            ]

            if len(predictions_df.index) == 0:
                should_raise_for_confidence_bounds = True


        if should_raise_for_predicted_value:

            self.assertTrue(should_raise_for_confidence_bounds)

            # Computing prediction based optima should fail if the surrogate model is not fitted.
            #
            with self.assertRaises(ValueError):
                optimizer.optimum(OptimumDefinition.PREDICTED_VALUE_FOR_OBSERVED_CONFIG)

        else:
            predicted_best_config, predicted_optimum = optimizer.optimum(OptimumDefinition.PREDICTED_VALUE_FOR_OBSERVED_CONFIG)

        if should_raise_for_confidence_bounds:

            with self.assertRaises(ValueError):
                optimizer.optimum(OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG)

            with self.assertRaises(ValueError):
                optimizer.optimum(OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG)
        else:
            ucb_90_ci_config, ucb_90_ci_optimum = optimizer.optimum(OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.1)
            ucb_95_ci_config, ucb_95_ci_optimum = optimizer.optimum(OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.05)
            ucb_99_ci_config, ucb_99_ci_optimum = optimizer.optimum(OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.01)

            lcb_90_ci_config, lcb_90_ci_optimum = optimizer.optimum(OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.1)
            lcb_95_ci_config, lcb_95_ci_optimum = optimizer.optimum(OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.05)
            lcb_99_ci_config, lcb_99_ci_optimum = optimizer.optimum(OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG, alpha=0.01)


            # At the very least we can assert the ordering. Note that the configs corresponding to each of the below confidence bounds can be different, as confidence intervals
            # change width non-linearily both with degrees of freedom, and with prediction variance.
            #
            if not (lcb_99_ci_optimum.lower_confidence_bound <= lcb_95_ci_optimum.lower_confidence_bound <= lcb_90_ci_optimum.lower_confidence_bound <= predicted_optimum.predicted_value):
                # If the the prediction for predicted_value has too few degrees of freedom, it's impossible to construct a confidence interval for it.
                # If it was possible, then the inequality above would always hold. If it's not possible, then the inequality above can fail.
                #
                optimum_predicted_value_prediction = optimizer.predict(feature_values_pandas_frame=predicted_best_config.to_dataframe())
                optimum_predicted_value_prediction_df = optimum_predicted_value_prediction.get_dataframe()
                degrees_of_freedom = optimum_predicted_value_prediction_df[Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value][0]
                if degrees_of_freedom == 0:
                    self.assertTrue(lcb_99_ci_optimum.lower_confidence_bound <= lcb_95_ci_optimum.lower_confidence_bound <= lcb_90_ci_optimum.lower_confidence_bound)
                else:
                    print(lcb_99_ci_optimum.lower_confidence_bound, lcb_95_ci_optimum.lower_confidence_bound, lcb_90_ci_optimum.lower_confidence_bound, predicted_optimum.predicted_value)
                    self.assertTrue(False)

            if not (predicted_optimum.predicted_value <= ucb_90_ci_optimum.upper_confidence_bound <= ucb_95_ci_optimum.upper_confidence_bound <= ucb_99_ci_optimum.upper_confidence_bound):
                optimum_predicted_value_prediction = optimizer.predict(feature_values_pandas_frame=predicted_best_config.to_dataframe())
                optimum_predicted_value_prediction_df = optimum_predicted_value_prediction.get_dataframe()
                degrees_of_freedom = optimum_predicted_value_prediction_df[Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value][0]
                if degrees_of_freedom == 0:
                    self.assertTrue(ucb_90_ci_optimum.upper_confidence_bound <= ucb_95_ci_optimum.upper_confidence_bound <= ucb_99_ci_optimum.upper_confidence_bound)
                else:
                    print(predicted_optimum.predicted_value, ucb_90_ci_optimum.upper_confidence_bound, ucb_95_ci_optimum.upper_confidence_bound, ucb_99_ci_optimum.upper_confidence_bound)
                    self.assertTrue(False)
