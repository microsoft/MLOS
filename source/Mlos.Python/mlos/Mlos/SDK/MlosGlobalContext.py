#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Mlos.Infrastructure import RegisterSmartComponentMessage, UnregisterSmartComponentMessage
from .Utils.Clock import Clock, ClockTick

class MlosGlobalContext:
    """ A singleton class keeping track of all live smart components, enabled telemetry.

    This object is also the owner of the target-side communication channel.

    Here are the goals for this object:

        INTERNAL facing (used by components in the process):
            1. To own all Mlos related resources in the target process.
            2. To own the SmartComponentManager, TelemetryManager, ConfigurationManager, RuntimeDecisionManager


        EXTERNAL facing (used by the Mlos.Agent):
            1. To establish and maintain a connection with the Mlos.Agent.

        Further:
            Each smart component creates an MlosObject, and queries it for config and for runtime decisions. The smart component
            is meant to remain oblivious to where the decisions come from. Smart components are also oblivious to who is looking
             at their telemetry.

             This means that we should be able to bind the MlosObject to different decision makers / observers at runtime.

             For example: while no experiment is in progress, we can serve the smart component pre-canned configurations or simple heuristics.
             Then, once an experiment is enabled, we can bind the decisions to be forwarded to Mlos.Agent and undertaken somewhere remotely.
             Then, once an experiment is finished, we could perhaps push down a new configuration, simple heuristic, or an in-process model and bind
             the decision maker to it.

        This is a lot of responsibility for a single class. I will break it into smaller classes with much more constrained responsibilities.

    The Mediator Pattern:
        To facilitate independent development of and loose coupling between all the managers, they will all utilize the MlosGlobalContext
        to refer to one another.

    """

    def __init__(
            self,
            communication_channel,
            shared_config,
    ):
        self._communication_channel = communication_channel

        #TODO: this is only temporary. Remove the direct APIs with message passing
        self._shared_config = shared_config
        self._shared_config.add_allowed_component(Clock, None)
        self._shared_config.enable_message_types(Clock, [ClockTick])

        self._clock = Clock(communication_channel=communication_channel, tick_frequency_ms=10)

    @property
    def communication_channel(self):
        return self._communication_channel

    @property
    def shared_config(self):
        return self._shared_config

    def start_clock(self):
        self._clock.start()

    def stop_clock(self):
        self._clock.stop()


    def register_mlos_object(self, mlos_object):
        """ Registers the component with the smart component manager.

        :param mlos_object:
        :return:
        """
        self._communication_channel.submit_message(
            RegisterSmartComponentMessage(
                component_type_name=mlos_object.owning_component_type.__name__,
                component_runtime_attributes=mlos_object.owning_component_runtime_attributes
            )
        )

        # Let's enable required telemetry
        mlos_object.disable_all_message_types()
        enabled_message_types = self._shared_config.get_enabled_message_types(mlos_object.owning_component_type)
        mlos_object.enable_message_types(enabled_message_types)

    def unregister_mlos_object(self, mlos_object):
        self._communication_channel.submit_message(
            UnregisterSmartComponentMessage(
                component_type_name=mlos_object.owning_component_type.__name__,
                component_runtime_attributes=mlos_object.owning_component_runtime_attributes
            )
        )

    def is_message_type_enabled(self, component_type, message_type):
        return self._shared_config.is_message_type_enabled(component_type, message_type)

    def send_telemetry_message(self, message):
        self._communication_channel.submit_message(message)

    def get_current_config(self, component_type):
        return self._shared_config.get_current_config(component_type)
