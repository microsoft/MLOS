#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
from threading import Thread
import unittest

import grpc
import mlos.global_values as global_values
from mlos.Grpc.OptimizerMicroserviceServer import OptimizerMicroserviceServer
from mlos.Grpc.BayesianOptimizerFactory import BayesianOptimizerFactory
from mlos.Logger import create_logger
from mlos.Examples.SmartCache import SmartCacheWorkloadGenerator, SmartCache
from mlos.Examples.SmartCache.TelemetryAggregators.WorkingSetSizeEstimator import WorkingSetSizeEstimator
from mlos.Mlos.Infrastructure import CommunicationChannel, SharedConfig
from mlos.Mlos.SDK import mlos_globals, MlosGlobalContext, MlosExperiment, MlosAgent
from mlos.Mlos.SDK.CommonAggregators.Timer import Timer
from mlos.Optimizers.BayesianOptimizer import BayesianOptimizerConfig
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import SimpleHypergrid, ContinuousDimension


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

        self.workload_duration_s = 5

        # Let's add the allowed component types
        self.mlos_agent.add_allowed_component_type(SmartCache)
        self.mlos_agent.add_allowed_component_type(SmartCacheWorkloadGenerator)

        # Let's create the workload
        self.smart_cache_workload = SmartCacheWorkloadGenerator(logger=self.logger)

        self.optimizer = None
        self.working_set_size_estimator = WorkingSetSizeEstimator()

        self.cache_config_timer = Timer(
            timeout_ms=200,
            observer_callback=self._set_new_cache_configuration
        )

        self.smart_cache_experiment = MlosExperiment(
            smart_component_types=[SmartCache],
            telemetry_aggregators=[self.cache_config_timer, self.working_set_size_estimator]
        )

        self.optimization_problem = OptimizationProblem(
            parameter_space=SmartCache.parameter_search_space,
            objective_space=SimpleHypergrid(name="objectives", dimensions=[
                ContinuousDimension(name="miss_rate", min=0, max=1)
            ]),
            context_space=None,  # TODO: add working set size estimate
            objectives=[Objective(name="miss_rate", minimize=True)]
        )

    def tearDown(self):
        mlos_globals.mlos_global_context.stop_clock()
        self.mlos_agent.stop_all()
        self.server.stop(grace=None)


    def test_smart_cache_with_remote_optimizer_on_a_timer(self):
        """ Periodically invokes the optimizer to improve cache performance.

        """
        self.optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
            optimization_problem=self.optimization_problem,
            optimizer_config=BayesianOptimizerConfig.DEFAULT
        )
        self.mlos_agent.start_experiment(self.smart_cache_experiment)

        # Let's launch the smart_cache_workload
        smart_cache_workload_thread = Thread(target=self.smart_cache_workload.run, args=(self.workload_duration_s,))
        smart_cache_workload_thread.start()
        smart_cache_workload_thread.join()

        self.mlos_agent.stop_experiment(self.smart_cache_experiment)

    def _set_new_cache_configuration(self, elapsed_time_ms):
        """ This is where we would potentially query the optimizer.

                    :param elapsed_time_ms:
                    :return:
                    """
        new_config_values = self.optimizer.suggest()
        self.mlos_agent.set_configuration(
            component_type=SmartCache,
            new_config_values=new_config_values
        )
        current_estimate = self.working_set_size_estimator.estimate_working_set_size()
        self.logger.info(f"Estimated working set size: {current_estimate.chapman_estimator}")
