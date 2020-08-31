#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from collections import namedtuple
from threading import Thread, RLock


from mlos.Mlos.Infrastructure import ConfigurationManager, RuntimeDecisionsManager, SmartComponentManager, TelemetryManager,\
    RegisterSmartComponentMessage, UnregisterSmartComponentMessage
from mlos.Mlos.Infrastructure.ExperimentManager import ExperimentManager


class MlosAgent:
    """ Akin to the actual Mlos.Agent.

    This is a prototype of how an experiment will work with Mlos E2E.
    Normally MlosAgent would live in a separate process and communicate
    with the TargetProcess via the communication channel. However we want to
    simplify the implementation of this POC and yet make sure that it reflects
    the final architecture.

    So: we will launch this MlosAgent in a separate thread, make sure it is
    attached to the communication channel (in-process), and has a sql-db endpoint
    to communicate with the Mlos.Service.

    """

    DoneProcessingMessage = namedtuple("DoneProcessing", [])



    def __init__(
            self,
            logger,
            communication_channel,
            shared_config,
            bayesian_optimizer_grpc_channel=None
    ):

        self.logger = logger
        # Note that in the native implementation, the interaction between the Mlos Agent and
        # the global mlos context is via the shared memory. Here we take a shortcut.
        self._communication_channel = communication_channel
        self._shared_config = shared_config
        self._bayesian_optimizer_grpc_channel = bayesian_optimizer_grpc_channel

        self._configuration_manager = ConfigurationManager(shared_config=self._shared_config)
        self._runtime_decision_manager = RuntimeDecisionsManager()
        self._smart_component_manager = SmartComponentManager()
        self._telemetry_manager = TelemetryManager(mlos_agent=self, shared_config=self._shared_config)

        # A dictionary mapping all message types to their respective callbacks:
        # * key: message_type
        # * value: List[callback_methods]
        self._message_callbacks_lock = RLock()
        self._message_callbacks = {
            self.DoneProcessingMessage: [self._raise_stop_iteration],
            RegisterSmartComponentMessage: [self._register_smart_component],
            UnregisterSmartComponentMessage: [self._unregister_smart_component]
        }
        self._callback_processor_thread = Thread(target=self._process_callbacks)

        self._experiment_manager = ExperimentManager(
            mlos_agent=self,
            communication_channel=communication_channel,
            logger=logger
        )

    def run(self):
        """
        This would be the new thread's entry point.
        Agents responsibility would be to check if there are any requested experiments in the mlos_service
        and if so:
          1) create necessary aggregators
          2) enable required telemetry
          3) associate requisite callbacks with each telemetry message type
          3.5) associate requisite decision makers with each runtime decision
          4) submit observations to mlos service
          5) consume config recommendations from mlos_service
          6) propagate config recommendations to the global_mlos_context in the target process
          7) forward runtime decision requests from target to mlos service
          8) forward runtime decisions from mlos service to target
        """

        self._callback_processor_thread.start()

    def stop_all(self):
        if self._callback_processor_thread is not None:
            self._communication_channel.submit_message(self.DoneProcessingMessage())
            self._callback_processor_thread.join()
            self._callback_processor_thread = None

    def start_experiment(self, mlos_experiment):
        """ Launches an Mlos TelemetryAggregators by.

        Steps:
        * Enable requested telemetry
        * Associate telemetry aggregators with telemetry events
        * Associate decision makers with each runtime decision


        :param mlos_experiment:
        :return:
        """
        self._experiment_manager.start_experiment(mlos_experiment)

    def stop_experiment(self, mlos_experiment):
        self._experiment_manager.stop_experiment(mlos_experiment)

    def add_allowed_component_type(self, component_type):
        # To make sure that the smart component manager knows what components can be managed
        self._smart_component_manager.add_allowed_component_type(component_type)

        # To make sure the configuration manager knows what the search space is and what the default config is
        self._configuration_manager.add_allowed_component_type(component_type)

        # To make sure that the telemetry manager knows what telemetry is available
        self._telemetry_manager.add_allowed_component_type(component_type)

    def enumerate_allowed_component_types(self):
        return self._smart_component_manager.enumerate_allowed_component_types()

    def enumerate_active_smart_components(self, component_selector=None):
        return self._smart_component_manager.enumerate_active_smart_components(component_selector=component_selector)

    def enable_telemetry_message_types(self, component_type, message_types):
        self._telemetry_manager.enable_message_types(component_type, message_types)

    def disable_telemetry_message_types(self, component_type, message_types):
        self._telemetry_manager.disable_message_types(component_type, message_types)

    def enumerate_enabled_telemetry_message_types(self):
        return self._telemetry_manager.enumerate_enabled_telemetry_message_types()

    def add_runtime_decision_maker(self, runtime_decision_maker):
        self._runtime_decision_manager.add_runtime_decision_maker(runtime_decision_maker)

    def remove_runtime_decision_maker(self, runtime_decision_maker):
        self._runtime_decision_manager.remove_runtime_decision_maker(runtime_decision_maker)

    def set_configuration(self, component_type, new_config_values):
        self._configuration_manager.set_configuration(
            component_type=component_type,
            new_config_values=new_config_values
        )

    def get_configuration(self, component_type):
        return self._configuration_manager.get_configuration(
            component_type=component_type
        )

    def register_callback(self, message_type, callback_method):
        with self._message_callbacks_lock:
            existing_callbacks = self._message_callbacks.get(message_type, [])
            existing_callbacks.append(callback_method)
            self._message_callbacks[message_type] = existing_callbacks

    def unregister_callback(self, message_type, callback_method):
        with self._message_callbacks_lock:
            existing_callbacks = self._message_callbacks.get(message_type, [])

            if callback_method in existing_callbacks:
                existing_callbacks.remove(callback_method)

            if not existing_callbacks and message_type in self._message_callbacks:
                del self._message_callbacks[message_type]

    def _process_callbacks(self):
        """ Reads from the communication channel

        :return:
        """
        self.logger.info("Starting processing telemetry messages.")
        try:
            for message in self._communication_channel:
                with self._message_callbacks_lock:
                    # TODO: we don't need to do this on every message call... we should have a local cache that we refresh only when necessary
                    registered_callbacks = self._message_callbacks.get(type(message), [])
                for callback in registered_callbacks:
                    callback(message)
        except StopIteration:
            self.logger.info("Finished processing telemetry messages")

    @staticmethod
    def _raise_stop_iteration(message):
        raise StopIteration

    def _register_smart_component(self, register_smart_component_message: RegisterSmartComponentMessage):
        """ Registers an active smart component with smart component manager.

        :param register_smart_component_message:
        :return:
        """
        self._smart_component_manager.register_smart_component(
            register_smart_component_message.component_type_name,
            register_smart_component_message.component_runtime_attributes
        )

    def _unregister_smart_component(self, unregister_smart_component_messsage: UnregisterSmartComponentMessage):
        self._smart_component_manager.unregister_smart_component(
            unregister_smart_component_messsage.component_type_name,
            unregister_smart_component_messsage.component_runtime_attributes
        )
