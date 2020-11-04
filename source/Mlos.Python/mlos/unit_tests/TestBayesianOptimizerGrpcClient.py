#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import unittest
import warnings

import grpc
import numpy as np
import pandas as pd


import mlos.global_values as global_values
from mlos.Grpc.OptimizerMicroserviceServer import OptimizerMicroserviceServer
from mlos.Grpc.OptimizerMonitor import OptimizerMonitor
from mlos.Grpc.OptimizerService_pb2 import Empty
from mlos.Grpc.OptimizerService_pb2_grpc import OptimizerServiceStub
from mlos.Logger import create_logger
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.Optimizers.BayesianOptimizer import bayesian_optimizer_config_store
from mlos.Optimizers.BayesianOptimizerFactory import BayesianOptimizerFactory
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective


class TestBayesianOptimizerGrpcClient(unittest.TestCase):
    """ Tests the E2E Grpc Client-Service workflow.

    """

    @classmethod
    def setUpClass(cls):
        warnings.simplefilter("error")
        global_values.declare_singletons()

    def setUp(self):
        self.logger = create_logger(self.__class__.__name__)
        # Start up the gRPC service.
        #
        self.server = OptimizerMicroserviceServer(port=50051, num_threads=10)
        self.server.start()

        self.optimizer_service_channel = grpc.insecure_channel('localhost:50051')
        self.bayesian_optimizer_factory = BayesianOptimizerFactory(grpc_channel=self.optimizer_service_channel, logger=self.logger)
        self.optimizer_monitor = OptimizerMonitor(grpc_channel=self.optimizer_service_channel, logger=self.logger)

        objective_function_config = objective_function_config_store.get_config_by_name('2d_quadratic_concave_up')
        self.objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config)

        self.optimization_problem = OptimizationProblem(
            parameter_space=self.objective_function.parameter_space,
            objective_space=self.objective_function.output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

    def tearDown(self):
        """ We need to tear down the gRPC server here.

        :return:
        """
        self.server.stop(grace=None)

    def test_echo(self):
        optimizer_service_stub = OptimizerServiceStub(channel=self.optimizer_service_channel)
        response = optimizer_service_stub.Echo(Empty())
        self.assertTrue(isinstance(response, Empty))


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

        self.assertTrue(len(new_optimizers) == 1)

        new_optimizer_id = list(new_optimizers.keys())[0]
        new_optimizer = new_optimizers[new_optimizer_id]

        self.assertTrue(new_optimizer_id == bayesian_optimizer.id)
        self.assertTrue(new_optimizer.optimizer_config == bayesian_optimizer.optimizer_config)

        num_iterations = 100
        registered_features_df, registered_objectives_df = self.optimize_quadratic(optimizer=bayesian_optimizer, num_iterations=num_iterations)

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

        observed_features_df, observed_objectives_df = bayesian_optimizer.get_all_observations()

        self.assertTrue((np.abs(registered_features_df - observed_features_df) < 0.00000001).all().all())
        self.assertTrue((np.abs(registered_objectives_df - observed_objectives_df) < 0.00000001).all().all())

        # Let's look at the goodness of fit.
        #
        random_forest_gof_metrics = bayesian_optimizer.compute_surrogate_model_goodness_of_fit()

        # The model might not have used all of the samples, but should have used a majority of them (I expect about 90%), but 70% is a good sanity check
        # and should make this test not very flaky.
        self.assertTrue(random_forest_gof_metrics.last_refit_iteration_number > 0.7 * num_iterations)

        # The invariants below should be true for all surrogate models: the random forest, and all constituent decision trees. So let's iterate over them all.
        models_gof_metrics = [random_forest_gof_metrics]

        for model_gof_metrics in models_gof_metrics:
            self.assertTrue(0 <= model_gof_metrics.relative_absolute_error <= 1) # This could fail if the models are really wrong. Not expected in this unit test though.
            self.assertTrue(0 <= model_gof_metrics.relative_squared_error <= 1)

            # There is an invariant linking mean absolute error (MAE), root mean squared error (RMSE) and number of observations (n) let's assert it.
            n = model_gof_metrics.last_refit_iteration_number
            self.assertTrue(model_gof_metrics.mean_absolute_error <= model_gof_metrics.root_mean_squared_error <= math.sqrt(n) * model_gof_metrics.mean_absolute_error)

            # We know that the sample confidence interval is wider (or equal to) prediction interval. So hit rates should be ordered accordingly.
            self.assertTrue(model_gof_metrics.sample_90_ci_hit_rate >= model_gof_metrics.prediction_90_ci_hit_rate)
            self.assertTrue(0 <= model_gof_metrics.coefficient_of_determination <= 1)


    def test_optimizer_with_random_config(self):
        num_random_restarts = 10
        for i in range(num_random_restarts):
            optimizer_config = bayesian_optimizer_config_store.parameter_space.random()

            optimizer_config.min_samples_required_for_guided_design_of_experiments = min(optimizer_config.min_samples_required_for_guided_design_of_experiments, 100)
            if optimizer_config.surrogate_model_implementation == "HomogeneousRandomForestRegressionModel":
                rf_config = optimizer_config.homogeneous_random_forest_regression_model_config
                rf_config.n_estimators = min(rf_config.n_estimators, 20)

            print(f"[{i+1}/{num_random_restarts}] Creating a bayesian optimizer with config: {optimizer_config}")

            bayesian_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
                optimization_problem=self.optimization_problem,
                optimizer_config=optimizer_config
            )
            registered_features_df, registered_objectives_df = self.optimize_quadratic(optimizer=bayesian_optimizer, num_iterations=12)

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

            observed_features_df, observed_objectives_df = bayesian_optimizer.get_all_observations()

            self.assertTrue((np.abs(registered_features_df - observed_features_df) < 0.00000001).all().all())
            self.assertTrue((np.abs(registered_objectives_df - observed_objectives_df) < 0.00000001).all().all())


    @unittest.skip(reason="Not implemented yet.")
    def test_optimizer_with_named_config(self):
        ...

    def optimize_quadratic(self, optimizer, num_iterations):
        registered_features_df = None
        registered_objectives_df = None
        old_optimum = np.inf
        for i in range(num_iterations):
            suggested_params = optimizer.suggest()
            suggested_params_df = suggested_params.to_dataframe()
            y = self.objective_function.evaluate_point(suggested_params)
            optimizer.register(suggested_params_df, y.to_dataframe())
            if registered_features_df is None:
                registered_features_df = suggested_params_df
            else:
                registered_features_df = registered_features_df.append(suggested_params_df, ignore_index=True)

            if registered_objectives_df is None:
                registered_objectives_df = y.to_dataframe()
            else:
                registered_objectives_df = registered_objectives_df.append(y.to_dataframe(), ignore_index=True)

            best_params, optimum = optimizer.optimum()
            # ensure current optimum doesn't go up
            assert optimum.y <= old_optimum
            old_optimum = optimum.y
            print(f"[{i+1}/{num_iterations}]Best Params: {best_params}, Best Value: {optimum.y}")
        return registered_features_df, registered_objectives_df
