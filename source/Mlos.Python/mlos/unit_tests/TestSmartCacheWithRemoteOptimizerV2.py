#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
import os
from threading import Thread
import unittest


from mlos.Logger import create_logger

from mlos.Examples.SmartCache import SmartCacheWorkloadGenerator, SmartCache
from mlos.Examples.SmartCache.TelemetryAggregators.WorkingSetSizeEstimator import WorkingSetSizeEstimator

from mlos.MlosOptimizationServices.MlosOptimizationServicesProxy import MlosOptimizationServicesProxy
from mlos.MlosOptimizationServices.ModelsDatabase.ConnectionString import ConnectionString

from mlos.Mlos.Infrastructure import CommunicationChannel, SharedConfig
from mlos.Mlos.SDK import mlos_globals, MlosGlobalContext, MlosExperiment, MlosAgent
from mlos.Mlos.SDK.CommonAggregators.Timer import Timer

from mlos.Optimizers.DistributableSimpleBayesianOptimizer import DistributableSimpleBayesianOptimizer
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import Point, SimpleHypergrid, ContinuousDimension

import mlos.global_values as global_values

class TestSmartCacheWithRemoteOptimizer(unittest.TestCase):
    """ Tests SmartCache that's being tuned by the remote optimizer.

    This test will:
    1. Instantiate a SmartCache.
    2. Create an MlosExperiment that connects to a remote or in-process optimizer.
    3. Optimize the SmartCache with the help of the remote or in-process optimizer.
    """

    def setUp(self):
        self.logger = create_logger('TestSmartCacheWithRemoteOptimizer')
        self.logger.level = logging.INFO

        self.communication_channel = CommunicationChannel()
        self.shared_config = SharedConfig()
        self.mlos_agent = MlosAgent(
            logger=self.logger,
            communication_channel=self.communication_channel,
            shared_config=self.shared_config,
            mlos_service_endpoint=None
        )

        self.mlos_global_context = MlosGlobalContext(
            communication_channel=self.communication_channel,
            shared_config=self.shared_config
        )

        self.mlos_agent_thread = Thread(target=self.mlos_agent.run)
        self.mlos_agent_thread.start()

        mlos_globals.init_mlos_global_context()
        mlos_globals.mlos_global_context = self.mlos_global_context

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
        self.mlos_global_context.stop_clock()
        self.mlos_agent.stop_all()


    @unittest.skip(reason="SQL Server is not available in GCI at the moment.")
    def test_smart_cache_with_remote_optimizer_on_a_timer(self):
        """ Periodically invokes the optimizer to improve cache performance.

        """

        # Let's create an optimizer
        connection_string = ConnectionString.create_from_config_file(os.path.abspath(os.path.join(os.getcwd(), "Secrets", "local_connection_string.json")))
        global_values.ml_model_services_proxy = MlosOptimizationServicesProxy(models_database_connection_string=connection_string)


        self.optimizer = DistributableSimpleBayesianOptimizer.create_remote_model(
            models_database=global_values.ml_model_services_proxy.models_database,
            optimization_problem=self.optimization_problem
        )

        TODO = """ There are so many things wrong here that an essay is in order.

        1. The entire DistributableSimpleBayesianOptimizer is to be thrown out.
        2. We need an Optimizer API that:
            1. Will be standard across many types of optimizers.
            2. Will let us specify:
                1. The search space
                2. The context space
                3. The target values

        We should generate client libraries along with MlosModelServices for Python and C# (at least). I suppose that's
        the next task after this test is turned on.
        """


        self.mlos_agent.start_experiment(self.smart_cache_experiment)

        # Let's launch the smart_cache_workload
        smart_cache_workload_thread = Thread(target=self.smart_cache_workload.run, args=(self.workload_duration_s,))
        smart_cache_workload_thread.start()
        smart_cache_workload_thread.join()

        self.mlos_agent.stop_experiment(self.smart_cache_experiment)

    def test_smart_cache_with_in_process_optimizer_on_a_timer2(self):
        """ Periodically invokes the optimizer to improve cache performance.

        """

        # Let's create an optimizer
        self.optimizer = DistributableSimpleBayesianOptimizer(
            optimization_problem=self.optimization_problem
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
        new_config_values = Point(**new_config_values)  # TODO: this Point() should not be necessary here
        self.mlos_agent.set_configuration(
            component_type=SmartCache,
            new_config_values=new_config_values
        )
        current_estimate = self.working_set_size_estimator.estimate_working_set_size()
        self.logger.info(f"Estimated working set size: {current_estimate.chapman_estimator}")