#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
from threading import Thread
import time
import unittest

from mlos.Logger import create_logger

from mlos.Examples.SmartCache import SmartCacheWorkloadGenerator, SmartCache
from mlos.Examples.SmartCache.TelemetryAggregators.WorkingSetSizeEstimator import WorkingSetSizeEstimator

from mlos.Mlos.Infrastructure import CommunicationChannel, SharedConfig
from mlos.Mlos.SDK import mlos_globals, MlosGlobalContext, MlosExperiment, MlosAgent
from mlos.Mlos.SDK.CommonAggregators.Timer import Timer

class TestE2EScenarios(unittest.TestCase):
    """ Tests aggregators based on the timer.

    """

    @classmethod
    def setUpClass(cls) -> None:
        mlos_globals.init_mlos_global_context()
        cls.logger = create_logger('TestE2EScenarios')
        cls.logger.level = logging.INFO
        cls.mlos_agent = MlosAgent(
            logger=cls.logger,
            communication_channel=mlos_globals.mlos_global_context.communication_channel,
            shared_config=mlos_globals.mlos_global_context.shared_config
        )
        cls.mlos_agent_thread = Thread(target=cls.mlos_agent.run)
        cls.mlos_agent_thread.start()
        mlos_globals.mlos_global_context.start_clock()
        cls.mlos_agent.add_allowed_component_type(SmartCache)
        cls.mlos_agent.add_allowed_component_type(SmartCacheWorkloadGenerator)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.mlos_agent.stop_all()
        mlos_globals.mlos_global_context.stop_clock()

    def test_timer(self):
        """ Tests if the timer works with required precision.

        :return:
        """
        timeout_ms = 100
        epsilon_ms = 10

        def _process_clock_event(elapsed_time_ms):
            self.assertTrue(elapsed_time_ms + epsilon_ms > timeout_ms)
            self.logger.debug(f"Processed clock event. Elapsed time: {elapsed_time_ms}")

        timer = Timer(
            timeout_ms=timeout_ms,
            observer_callback=_process_clock_event,
            epsilon_ms=epsilon_ms
        )

        timer_experiment = MlosExperiment(
            smart_component_types=[],
            telemetry_aggregators=[timer]
        )
        self.mlos_agent.start_experiment(timer_experiment)
        time.sleep(1)
        self.mlos_agent.stop_experiment(timer_experiment)

    def test_setting_random_configs_for_smart_cache_workload(self):

        workload_duration_s = 1
        # Let's launch the smart_cache_workload
        smart_cache_workload = SmartCacheWorkloadGenerator(logger=self.logger)
        self.current_workload_config_values = smart_cache_workload.current_config.values
        smart_cache_workload_thread = Thread(target=smart_cache_workload.run, args=(workload_duration_s,))
        smart_cache_workload_thread.start()

        def _set_random_workload_configuration(elapsed_time_ms):
            new_config_values = SmartCacheWorkloadGenerator.parameter_search_space.random()
            self.mlos_agent.set_configuration(
                component_type=SmartCacheWorkloadGenerator,
                new_config_values=new_config_values
            )
            self.current_workload_config_values = new_config_values

        timer = Timer(
            timeout_ms=100,
            observer_callback=_set_random_workload_configuration
        )

        random_workload_config_experiment = MlosExperiment(
            smart_component_types=[SmartCacheWorkloadGenerator],
            telemetry_aggregators=[timer]
        )

        self.mlos_agent.start_experiment(random_workload_config_experiment)
        time.sleep(workload_duration_s)
        self.mlos_agent.stop_experiment(random_workload_config_experiment)

    def test_setting_random_configs_for_smart_cache(self):
        workload_duration_s = 5

        # Let's create the workload
        smart_cache_workload = SmartCacheWorkloadGenerator(logger=self.logger)

        def _set_random_cache_configuration(elapsed_time_ms):
            """ This is where we would potentially query the optimizer.

            :param elapsed_time_ms:
            :return:
            """
            new_config_values = SmartCache.parameter_search_space.random()
            self.mlos_agent.set_configuration(
                component_type=SmartCache,
                new_config_values=new_config_values
            )
            current_estimate = working_set_size_estimator.estimate_working_set_size()
            self.logger.info(f"Estimated working set size: {current_estimate.chapman_estimator}")

        cache_config_timer = Timer(
            timeout_ms=200,
            observer_callback=_set_random_cache_configuration
        )

        working_set_size_estimator = WorkingSetSizeEstimator()

        smart_cache_experiment = MlosExperiment(
            smart_component_types=[SmartCache],
            telemetry_aggregators=[cache_config_timer, working_set_size_estimator]
        )

        self.mlos_agent.start_experiment(smart_cache_experiment)
        ##################################################################################

        # Let's launch the smart_cache_workload
        smart_cache_workload_thread = Thread(target=smart_cache_workload.run, args=(workload_duration_s,))
        smart_cache_workload_thread.start()
        smart_cache_workload_thread.join()

        self.mlos_agent.stop_experiment(smart_cache_experiment)

    def test_setting_random_configs_for_smart_cache_and_for_smart_cache_workload(self):
        """ Enables two experiments at once: one to set the cache parameters, the other to set the workload parameters.

        :return:
        """
        workload_duration_s = 2


        # Let's create the workload
        smart_cache_workload = SmartCacheWorkloadGenerator(logger=self.logger)
        self.current_workload_config_values = smart_cache_workload.current_config.values

        ##################################################################################
        # Let's configure the expriment changing the workload configuration
        def _set_random_workload_configuration(elapsed_time_ms):
            # First check that the config has been consumed
            #if smart_cache_workload.current_config.values != self.current_workload_config_values:
            #    print("Put breakpoint here.")
            #self.assertTrue(smart_cache_workload.current_config.values == self.current_workload_config_values)

            new_config_values = SmartCacheWorkloadGenerator.parameter_search_space.random()
            self.mlos_agent.set_configuration(
                component_type=SmartCacheWorkloadGenerator,
                new_config_values=new_config_values
            )
            self.current_workload_config_values = new_config_values

        workload_timer = Timer(
            timeout_ms=100,
            observer_callback=_set_random_workload_configuration
        )

        random_workload_config_experiment = MlosExperiment(
            smart_component_types=[SmartCacheWorkloadGenerator],
            telemetry_aggregators=[workload_timer]
        )

        self.mlos_agent.start_experiment(random_workload_config_experiment)

        ##################################################################################
        # Now let's configure the smart cache tuning experiment

        def _set_random_cache_configuration(elapsed_time_ms):
            """ This is where we would potentially query the optimizer.

            :param elapsed_time_ms:
            :return:
            """
            new_config_values = SmartCache.parameter_search_space.random()
            self.mlos_agent.set_configuration(
                component_type=SmartCache,
                new_config_values=new_config_values
            )
            current_estimate = working_set_size_estimator.estimate_working_set_size()
            self.logger.info(f"Estimated working set size: {current_estimate.chapman_estimator}")

        cache_config_timer = Timer(
            timeout_ms=200,
            observer_callback=_set_random_cache_configuration
        )

        working_set_size_estimator = WorkingSetSizeEstimator()

        smart_cache_experiment = MlosExperiment(
            smart_component_types=[SmartCache],
            telemetry_aggregators=[cache_config_timer, working_set_size_estimator]
        )

        self.mlos_agent.start_experiment(smart_cache_experiment)
        ##################################################################################

        # Let's launch the smart_cache_workload
        smart_cache_workload_thread = Thread(target=smart_cache_workload.run, args=(workload_duration_s,))
        smart_cache_workload_thread.start()

        time.sleep(workload_duration_s)
        self.mlos_agent.stop_experiment(smart_cache_experiment)
        self.mlos_agent.stop_experiment(random_workload_config_experiment)

        smart_cache_workload_thread.join()

        all_registered_mlos_objects = set((component_type, runtime_attributes) for component_type ,runtime_attributes in self.mlos_agent.enumerate_active_smart_components())
        self.assertTrue(
            (smart_cache_workload.mlos_object.owning_component_type, smart_cache_workload.mlos_object.owning_component_runtime_attributes)
            in all_registered_mlos_objects
        )

        del smart_cache_workload
        self.mlos_agent.stop_all()

        all_registered_mlos_objects = set(mlos_object for mlos_object in self.mlos_agent.enumerate_active_smart_components())
        if len(all_registered_mlos_objects) != 0:
            print("Put breakpoint here")
        self.assertTrue(len(all_registered_mlos_objects) == 0)
