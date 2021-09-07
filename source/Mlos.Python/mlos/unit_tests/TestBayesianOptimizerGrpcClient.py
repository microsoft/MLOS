#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import pytest
import warnings

import grpc
import numpy as np
import pandas as pd


import mlos.global_values as global_values
from mlos.Grpc.OptimizerServicesServer import OptimizerServicesServer
from mlos.Grpc.OptimizerMonitor import OptimizerMonitor
from mlos.Grpc.OptimizerService_pb2 import Empty
from mlos.Grpc.OptimizerService_pb2_grpc import OptimizerServiceStub
from mlos.Logger import create_logger
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.Optimizers.BayesianOptimizer import bayesian_optimizer_config_store
from mlos.Optimizers.BayesianOptimizerFactory import BayesianOptimizerFactory
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionEnhancedRandomForest import MultiObjectiveRegressionEnhancedRandomForest


class TestBayesianOptimizerGrpcClient:
    """ Tests the E2E Grpc Client-Service workflow.

    """

    @classmethod
    def setup_class(cls):
        warnings.simplefilter("error")
        global_values.declare_singletons()

    def setup_method(self, method):
        self.logger = create_logger(self.__class__.__name__)

        # Start up the gRPC service. Try a bunch of times before giving up.
        #
        max_num_tries = 100
        num_tries = 0
        for port in range(50051, 50051 + max_num_tries):
            num_tries += 1
            try:
                self.server = OptimizerServicesServer(port=port, num_threads=10)
                self.server.start()
                self.port = port
                break
            except:
                self.logger.info(f"Failed to create OptimizerMicroserviceServer on port {port}")
                if num_tries == max_num_tries:
                    raise

        self.optimizer_service_channel = grpc.insecure_channel(f'localhost:{self.port}')
        self.bayesian_optimizer_factory = BayesianOptimizerFactory(grpc_channel=self.optimizer_service_channel, logger=self.logger)
        self.optimizer_monitor = OptimizerMonitor(grpc_channel=self.optimizer_service_channel, logger=self.logger)

        objective_function_config = objective_function_config_store.get_config_by_name('2d_quadratic_concave_up')
        self.objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config)

        self.optimization_problem = OptimizationProblem(
            parameter_space=self.objective_function.parameter_space,
            objective_space=self.objective_function.output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

    def teardown_method(self, method):
        """ We need to tear down the gRPC server here.

        :return:
        """
        self.server.stop(grace=None).wait(timeout=1)
        self.server.wait_for_termination(timeout=1)
        self.optimizer_service_channel.close()


    def test_echo(self):
        optimizer_service_stub = OptimizerServiceStub(channel=self.optimizer_service_channel)
        response = optimizer_service_stub.Echo(Empty())
        assert isinstance(response, Empty)


    def test_optimizer_with_default_config(self):
        pre_existing_optimizers = {optimizer.id: optimizer for optimizer in self.optimizer_monitor.get_existing_optimizers()}
        print(bayesian_optimizer_config_store.default)
        bayesian_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
            optimization_problem=self.optimization_problem,
            optimizer_config=bayesian_optimizer_config_store.default
        )
        post_existing_optimizers = {optimizer.id: optimizer for optimizer in self.optimizer_monitor.get_existing_optimizers()}

        new_optimizers = {
            optimizer_id: optimizer
            for optimizer_id, optimizer in post_existing_optimizers.items()
            if optimizer_id not in pre_existing_optimizers
        }

        assert len(new_optimizers) == 1

        new_optimizer_id = list(new_optimizers.keys())[0]
        new_optimizer = new_optimizers[new_optimizer_id]

        assert new_optimizer_id == bayesian_optimizer.id
        assert new_optimizer.optimizer_config == bayesian_optimizer.optimizer_config

        num_iterations = 100
        registered_features_df, registered_objectives_df = self.optimize_objective_function(optimizer=bayesian_optimizer, objective_function=self.objective_function, num_iterations=num_iterations)

        # Apparently the to_json/from_json loses precision so we explicitly lose it here so that we can do the comparison.
        #
        registered_features_json = registered_features_df.to_json(orient='index', double_precision=15)
        registered_objectives_json = registered_objectives_df.to_json(orient='index', double_precision=15)

        # Apparently the jitter is too good and we actually have to use the json strings or they will be optimized away.
        #
        assert len(registered_features_json) > 0
        assert len(registered_objectives_json) > 0

        registered_features_df = pd.read_json(registered_features_json, orient='index')
        registered_objectives_df = pd.read_json(registered_objectives_json, orient='index')

        observed_features_df, observed_objectives_df, _ = bayesian_optimizer.get_all_observations()

        assert (np.abs(registered_features_df - observed_features_df) < 0.00000001).all().all()
        assert (np.abs(registered_objectives_df - observed_objectives_df) < 0.00000001).all().all()

        # Assert that the observations and predictions are returned in the right order from the remote optimizer
        #
        parameters_df, objectives_df, _ = bayesian_optimizer.get_all_observations()
        predictions_df = bayesian_optimizer.predict(parameter_values_pandas_frame=parameters_df).get_dataframe()
        assert parameters_df.index.intersection(predictions_df.index).equals(predictions_df.index)

        # Let's look at the goodness of fit.
        #
        multi_objective_gof_metrics = bayesian_optimizer.compute_surrogate_model_goodness_of_fit()
        for objective_name, random_forest_gof_metrics in multi_objective_gof_metrics:

            # The model might not have used all of the samples, but should have used a majority of them (I expect about 90%), but 50% is a good sanity check
            # and should make this test not very flaky.
            assert random_forest_gof_metrics.last_refit_iteration_number > 0.5 * num_iterations

            # The invariants below should be true for all surrogate models: the random forest, and all constituent decision trees. So let's iterate over them all.
            models_gof_metrics = [random_forest_gof_metrics]

            for model_gof_metrics in models_gof_metrics:
                assert 0 <= model_gof_metrics.relative_absolute_error <= 1 # This could fail if the models are really wrong. Not expected in this unit test though.
                assert 0 <= model_gof_metrics.relative_squared_error <= 1

                # There is an invariant linking mean absolute error (MAE), root mean squared error (RMSE) and number of observations (n) let's assert it.
                n = model_gof_metrics.last_refit_iteration_number
                assert model_gof_metrics.mean_absolute_error <= model_gof_metrics.root_mean_squared_error <= math.sqrt(n) * model_gof_metrics.mean_absolute_error

                # We know that the sample confidence interval is wider (or equal to) prediction interval. So hit rates should be ordered accordingly.
                assert model_gof_metrics.sample_90_ci_hit_rate >= model_gof_metrics.prediction_90_ci_hit_rate
                assert 0 <= model_gof_metrics.coefficient_of_determination <= 1


    @pytest.mark.parametrize("i", [i for i in range(10)])
    def test_optimizer_with_random_config(self, i):
        optimizer_config = bayesian_optimizer_config_store.parameter_space.random()

        optimizer_config.min_samples_required_for_guided_design_of_experiments = max(min(optimizer_config.min_samples_required_for_guided_design_of_experiments, 100), 20)
        if optimizer_config.surrogate_model_implementation == "HomogeneousRandomForestRegressionModel":
            rf_config = optimizer_config.homogeneous_random_forest_regression_model_config
            rf_config.n_estimators = min(rf_config.n_estimators, 20)

        if optimizer_config.surrogate_model_implementation == MultiObjectiveRegressionEnhancedRandomForest.__name__:
            optimizer_config.min_samples_required_for_guided_design_of_experiments = 25
            rerf_model_config = optimizer_config.regression_enhanced_random_forest_regression_model_config
            rerf_model_config.max_basis_function_degree = min(rerf_model_config.max_basis_function_degree, 2)
            # increased polynomial degree requires more data to estimate model parameters (poly term coefficients)
            optimizer_config.min_samples_required_for_guided_design_of_experiments += 25 * (rerf_model_config.max_basis_function_degree - 1)
            rf_model_config = rerf_model_config.sklearn_random_forest_regression_model_config
            rf_model_config.perform_initial_random_forest_hyper_parameter_search = False
            rf_model_config.max_depth = min(rf_model_config.max_depth, 10)
            rf_model_config.n_jobs = min(rf_model_config.n_jobs, 4)
        print(f"[{i+1}] Creating a bayesian optimizer with config: {optimizer_config}")

        bayesian_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
            optimization_problem=self.optimization_problem,
            optimizer_config=optimizer_config
        )
        registered_features_df, registered_objectives_df = self.optimize_objective_function(optimizer=bayesian_optimizer, objective_function=self.objective_function, num_iterations=12)

        # Apparently the to_json/from_json loses precision so we explicitly lose it here so that we can do the comparison.
        #
        registered_features_json = registered_features_df.to_json(orient='index', double_precision=15)
        registered_objectives_json = registered_objectives_df.to_json(orient='index', double_precision=15)

        # Apparently the jitter is too good and we actually have to use the json strings or they will be optimized away.
        #
        assert len(registered_features_json) > 0
        assert len(registered_objectives_json) > 0

        registered_features_df = pd.read_json(registered_features_json, orient='index')
        registered_objectives_df = pd.read_json(registered_objectives_json, orient='index')

        observed_features_df, observed_objectives_df, _ = bayesian_optimizer.get_all_observations()

        assert (np.abs(registered_features_df - observed_features_df) < 0.00000001).all().all()
        assert (np.abs(registered_objectives_df - observed_objectives_df) < 0.00000001).all().all()

    @pytest.mark.parametrize("i", [i for i in range(10)])
    def test_optimizer_with_random_config_random_objective(self, i):
        objective_function_config = objective_function_config_store.parameter_space.random()
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config)
        optimization_problem = objective_function.default_optimization_problem


        optimizer_config = bayesian_optimizer_config_store.parameter_space.random()

        optimizer_config.min_samples_required_for_guided_design_of_experiments = min(optimizer_config.min_samples_required_for_guided_design_of_experiments, 100)
        if optimizer_config.surrogate_model_implementation == "HomogeneousRandomForestRegressionModel":
            rf_config = optimizer_config.homogeneous_random_forest_regression_model_config
            rf_config.n_estimators = min(rf_config.n_estimators, 20)

        print(f"[{i+1}] Creating a bayesian optimizer with config: {optimizer_config} \n\n\nObjective function config: {objective_function_config}")

        bayesian_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config
        )
        registered_params_df, registered_objectives_df = self.optimize_objective_function(optimizer=bayesian_optimizer, objective_function=objective_function, num_iterations=20)

        # Apparently the to_json/from_json loses precision so we explicitly lose it here so that we can do the comparison.
        #
        registered_features_json = registered_params_df.to_json(orient='index', double_precision=15)
        registered_objectives_json = registered_objectives_df.to_json(orient='index', double_precision=15)

        # Apparently the jitter is too good and we actually have to use the json strings or they will be optimized away.
        #
        assert len(registered_features_json) > 0
        assert len(registered_objectives_json) > 0

        registered_params_df = pd.read_json(registered_features_json, orient='index')
        registered_objectives_df = pd.read_json(registered_objectives_json, orient='index')

        observed_params_df, observed_objectives_df, _ = bayesian_optimizer.get_all_observations()

        numeric_params_names = [
            dimension.name
            for dimension
            in optimization_problem.parameter_space.dimensions
            if
                (isinstance(dimension, (ContinuousDimension, DiscreteDimension)) or (isinstance(dimension, CategoricalDimension) and dimension.is_numeric))
                and
                (dimension.name in registered_params_df.columns)
                and
                (dimension.name in observed_params_df.columns)
        ]
        numeric_params_df = registered_params_df[numeric_params_names]
        observed_numeric_params_df = observed_params_df[numeric_params_names]

        assert (np.abs(numeric_params_df.fillna(0) - observed_numeric_params_df.fillna(0)) < 0.00000001).all().all()
        assert (np.abs(registered_objectives_df - observed_objectives_df) < 0.00000001).all().all()


    @staticmethod
    def optimize_objective_function(optimizer, objective_function, num_iterations):
        registered_features_df = None
        registered_objectives_df = None

        # Let's make sure that the optimum for the first objective doesn't get worse throughout the optimization loop.
        #
        first_objective = optimizer.optimization_problem.objectives[0]
        if first_objective.minimize:
            old_optimum = np.inf
        else:
            old_optimum = -np.inf

        for i in range(num_iterations):
            suggested_params = optimizer.suggest()
            suggested_params_df = suggested_params.to_dataframe()
            objective_values = objective_function.evaluate_point(suggested_params)
            optimizer.register(suggested_params_df, objective_values.to_dataframe())
            if registered_features_df is None:
                registered_features_df = suggested_params_df
            else:
                registered_features_df = registered_features_df.append(suggested_params_df, ignore_index=True)

            if registered_objectives_df is None:
                registered_objectives_df = objective_values.to_dataframe()
            else:
                registered_objectives_df = registered_objectives_df.append(objective_values.to_dataframe(), ignore_index=True)

            best_params, optimum = optimizer.optimum()
            # ensure current optimum doesn't go up
            #
            if first_objective.minimize:
                assert optimum[first_objective.name] <= old_optimum
            else:
                assert optimum[first_objective.name] >= old_optimum

            old_optimum = optimum[first_objective.name]
            print(f"[{i+1}/{num_iterations}]Best Params: {best_params}, Best Value: {optimum[first_objective.name]}")
        return registered_features_df, registered_objectives_df
