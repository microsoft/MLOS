#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
class TelemetryManager:
    """ Keeps track of all telemetry available and enabled in the target process.

    TelemetryManager is responsible for:

    1. Keeping track of available telemetry.
    2. Keeping track of telemetry events that have any subscribers.
    3. To allow Mlos.Agent to subscribe to / unsubscribe from telemetry events.
    """

    def __init__(self, mlos_agent, shared_config):
        self._mlos_agent = mlos_agent
        self._shared_config = shared_config
        # A dictionary where:
        # * the key is ComponentType
        # * the value is a set of message types
        self._allowed_components_telemetry_messages_types = dict()

        # A dictionary where:
        # * the key is ComponentType
        # * the value is a dict where:
        #   * key is message_type
        #   * value is ref_count
        self._enabled_message_types = dict()

    def add_allowed_component_type(self, component_type):
        if component_type in self._allowed_components_telemetry_messages_types:
            raise RuntimeError(f"Component of type {component_type.__name__} already allowed.")

        # Let's list all telemetry messages that this element could emit
        self._allowed_components_telemetry_messages_types[component_type] = set(component_type.telemetry_message_types)


    def enable_message_types(self, component_type, message_types):
        """ Enables telemetry messages of specified types.

        :param component_type:
        :param message_types:
        :return:
        """

        # First: increment the ref count for all message types that have been requested
        # Keep track of newly_enabled_message_types
        newly_enabled_message_types = set()

        enabled_message_types = self._enabled_message_types.get(component_type, dict())
        for message_type in message_types:
            num_subscribers = enabled_message_types.get(message_type, 0)
            if num_subscribers == 0:
                newly_enabled_message_types.add(message_type)
            enabled_message_types[message_type] = num_subscribers + 1
        self._enabled_message_types[component_type] = enabled_message_types

        self._shared_config.enable_message_types(component_type, newly_enabled_message_types)

    def disable_message_types(self, component_type, message_types):
        if component_type not in self._enabled_message_types:
            return

        enabled_message_types = self._enabled_message_types[component_type]

        # Let's decrement ref-counts for message_types
        # Keep track of message_types with no more subscribers
        message_types_with_no_subscribers = set()
        for message_type in message_types:
            ref_count = enabled_message_types[message_type]
            ref_count -= 1
            if ref_count == 0:
                message_types_with_no_subscribers.add(message_type)
                del enabled_message_types[message_type]
            else:
                enabled_message_types[message_type] = ref_count

        self._shared_config.disable_message_types(component_type, message_types_with_no_subscribers)

    def enumerate_enabled_telemetry_message_types(self):
        for component_type, enabled_message_types_dict in self._enabled_message_types.items():
            for message_type, num_subscribers in enabled_message_types_dict.items():
                yield component_type, message_type, num_subscribers
