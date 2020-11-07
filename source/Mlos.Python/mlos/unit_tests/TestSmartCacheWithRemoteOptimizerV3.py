#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
import math
from threading import Thread
import unittest

import grpc
import pandas as pd

import mlos.global_values as global_values
from mlos.Grpc.OptimizerMicroserviceServer import OptimizerMicroserviceServer
from mlos.Optimizers.BayesianOptimizerFactory import BayesianOptimizerFactory
from mlos.Logger import create_logger
from mlos.Examples.SmartCache import SmartCacheWorkloadGenerator, SmartCache, HitRateMonitor
from mlos.Examples.SmartCache.TelemetryAggregators.WorkingSetSizeEstimator import WorkingSetSizeEstimator
from mlos.Mlos.SDK import mlos_globals, MlosExperiment, MlosAgent
from mlos.Optimizers.BayesianOptimizer import bayesian_optimizer_config_store
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import ContinuousDimension, Point, SimpleHypergrid


class TestSmartCacheWithRemoteOptimizer(unittest.TestCase):
    """ Tests SmartCache that's being tuned by the remote optimizer.

    This test will:
    1. Instantiate a SmartCache.
    2. Create an MlosExperiment that connects to a remote or in-process optimizer.
    3. Optimize the SmartCache with the help of the remote or in-process optimizer.
    """

    def setUp(self):
        mlos_globals.init_mlos_global_context()
        mlos_globals.mlos_global_context.start_clock()
        self.logger = create_logger('TestSmartCacheWithRemoteOptimizer')
        self.logger.level = logging.DEBUG

        # Start up the gRPC service.
        #
        self.server = OptimizerMicroserviceServer(port=50051, num_threads=10)
        self.server.start()

        self.optimizer_service_grpc_channel = grpc.insecure_channel('localhost:50051')
        self.bayesian_optimizer_factory = BayesianOptimizerFactory(grpc_channel=self.optimizer_service_grpc_channel, logger=self.logger)

        self.mlos_agent = MlosAgent(
            logger=self.logger,
            communication_channel=mlos_globals.mlos_global_context.communication_channel,
            shared_config=mlos_globals.mlos_global_context.shared_config,
            bayesian_optimizer_grpc_channel=self.optimizer_service_grpc_channel
        )

        self.mlos_agent_thread = Thread(target=self.mlos_agent.run)
        self.mlos_agent_thread.start()

        global_values.declare_singletons()  # TODO: having both globals and global_values is a problem

        # Let's add the allowed component types
        self.mlos_agent.add_allowed_component_type(SmartCache)
        self.mlos_agent.add_allowed_component_type(SmartCacheWorkloadGenerator)
        self.mlos_agent.set_configuration(
            component_type=SmartCacheWorkloadGenerator,
            new_config_values=Point(
                workload_type='cyclical_key_from_range',
                cyclical_key_from_range_config=Point(
                    min=0,
                    range_width=2048
                )
            )
        )

        # Let's create the workload
        self.smart_cache_workload = SmartCacheWorkloadGenerator(logger=self.logger)

        self.optimizer = None
        self.working_set_size_estimator = WorkingSetSizeEstimator()
        self.hit_rate_monitor = HitRateMonitor()

        self.smart_cache_experiment = MlosExperiment(
            smart_component_types=[SmartCache],
            telemetry_aggregators=[self.working_set_size_estimator, self.hit_rate_monitor]
        )

        self.optimization_problem = OptimizationProblem(
            parameter_space=SmartCache.parameter_search_space,
            objective_space=SimpleHypergrid(name="objectives", dimensions=[ContinuousDimension(name="hit_rate", min=0, max=1)]),
            objectives=[Objective(name="hit_rate", minimize=False)]
        )

    def tearDown(self):
        mlos_globals.mlos_global_context.stop_clock()
        self.mlos_agent.stop_all()
        self.server.stop(grace=None)


    def test_smart_cache_with_remote_optimizer_on_a_timer(self):
        """ Periodically invokes the optimizer to improve cache performance.

        """
        optimizer_config = bayesian_optimizer_config_store.default
        optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.n_new_samples_before_refit = 5
        self.optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
            optimization_problem=self.optimization_problem,
            optimizer_config=optimizer_config
        )
        self.mlos_agent.start_experiment(self.smart_cache_experiment)


        num_iterations = 101
        for i in range(num_iterations):
            smart_cache_workload_thread = Thread(target=self.smart_cache_workload.run, args=(0.1,))
            smart_cache_workload_thread.start()
            smart_cache_workload_thread.join()

            current_cache_config = self.mlos_agent.get_configuration(component_type=SmartCache)
            features_df = current_cache_config.to_dataframe()
            hit_rate = self.hit_rate_monitor.get_hit_rate()
            num_requests = self.hit_rate_monitor.num_requests
            working_set_size_estimate = self.working_set_size_estimator.estimate_working_set_size()
            objectives_df = pd.DataFrame({'hit_rate': [hit_rate]})
            self.optimizer.register(features_df, objectives_df)
            new_config_values = self.optimizer.suggest()
            self.mlos_agent.set_configuration(component_type=SmartCache, new_config_values=new_config_values)
            self.hit_rate_monitor.reset()
            self.logger.info(f"Previous config: {current_cache_config.to_json()}")
            self.logger.info(f"Estimated working set size: {working_set_size_estimate.chapman_estimator}. Hit rate: {hit_rate:.2f}. Num requests: {num_requests} ")


        self.mlos_agent.stop_experiment(self.smart_cache_experiment)


        # Let's look at the goodness of fit.
        #
        random_forest_gof_metrics = self.optimizer.compute_surrogate_model_goodness_of_fit()

        # The model might not have used all of the samples, but should have used a majority of them (I expect about 90%), but 70% is a good sanity check
        # and should make this test not very flaky.
        self.assertTrue(random_forest_gof_metrics.last_refit_iteration_number > 0.7 * num_iterations)

        # The invariants below should be true for all surrogate models: the random forest, and all constituent decision trees. So let's iterate over them all.
        models_gof_metrics = [random_forest_gof_metrics]

        for model_gof_metrics in models_gof_metrics:
            # Those relative errors should generally be between 0 and 1 unless the model's predictions are worse than predicting average...
            # This unit tests occasionally doesn't have enough data to get us down to 1 so we'll pass the test if its less than 2.
            # Note, the point of this test is to check sanity. We'll use a separate suite to evaluate models' performance from an ML standpoint.
            self.logger.info(f"Relative absolute error: {model_gof_metrics.relative_absolute_error}")
            self.logger.info(f"Relative squared error: {model_gof_metrics.relative_squared_error}")
            self.assertTrue(model_gof_metrics.relative_absolute_error is None or (0 <= model_gof_metrics.relative_absolute_error <= 2))
            self.assertTrue(model_gof_metrics.relative_squared_error is None or (0 <= model_gof_metrics.relative_squared_error <= 2))

            # There is an invariant linking mean absolute error (MAE), root mean squared error (RMSE) and number of observations (n) let's assert it.
            n = model_gof_metrics.last_refit_iteration_number
            self.logger.info(f"Last refit iteration number: {n}")
            self.logger.info(f"Mean absolute error: {model_gof_metrics.mean_absolute_error}")
            self.logger.info(f"Root mean squared error: {model_gof_metrics.root_mean_squared_error}")
            self.assertTrue(model_gof_metrics.mean_absolute_error <= model_gof_metrics.root_mean_squared_error <= math.sqrt(n) * model_gof_metrics.mean_absolute_error)

            # We know that the sample confidence interval is wider (or equal to) prediction interval. So hit rates should be ordered accordingly.
            self.assertTrue(model_gof_metrics.sample_90_ci_hit_rate >= model_gof_metrics.prediction_90_ci_hit_rate)

