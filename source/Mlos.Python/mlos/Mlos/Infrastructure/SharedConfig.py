#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from threading import RLock

class SharedConfig:
    """ A view of config visible to both the Mlos Agent and the Target System

    """

    def __init__(self):
        # Maps component types with their default configs
        self._default_configurations = dict()

        # Maps component types with their current configs
        self._current_configurations = dict()

        # To ensure that config reads/updates are atomic
        self._configuration_locks = dict()

        # Mapping between component types and the telemetry message types enabled for them
        self._enabled_message_types = dict()

        self._message_type_locks = dict()

    def add_allowed_component(self, component_type, default_configuration):
        self._default_configurations[component_type] = default_configuration
        self._configuration_locks[component_type] = RLock()
        self._message_type_locks[component_type] = RLock()

    @property
    def allowed_component_types(self):
        return self._default_configurations.keys()

    def set_config(self, component_type, new_configuration):
        with self._configuration_locks[component_type]:
            self._current_configurations[component_type] = new_configuration

    def get_current_config(self, component_type):
        """ Returns the most up to date configuration for a given component group.

        The component group is identified by the component types and a combination of
        its runtime attributes.

        :param component_type:
        :return:
        """

        current_config = None
        # Note: this will throw if the component is not allowed - no need to throw explicitly for now
        if component_type in self._configuration_locks:
            with self._configuration_locks[component_type]:
                current_config = self._current_configurations.get(component_type, None)

        if current_config is not None:
            return current_config
        return self._default_configurations.get(component_type, None)

    def get_enabled_message_types(self, component_type):
        if component_type in self._message_type_locks:
            with self._message_type_locks[component_type]:
                return self._enabled_message_types.get(component_type, set())
        else:
            return set()

    def is_message_type_enabled(self, component_type, message_type):
        if component_type in self._enabled_message_types:
            with self._message_type_locks[component_type]:
                return message_type in self._enabled_message_types[component_type]
        return False

    def enable_message_types(self, component_type, message_types):
        with self._message_type_locks[component_type]:
            enabled_message_types = self._enabled_message_types.get(component_type, set())
            enabled_message_types = enabled_message_types.union(message_types)
            self._enabled_message_types[component_type] = enabled_message_types

    def disable_message_types(self, component_type, message_types):
        with self._message_type_locks[component_type]:
            enabled_message_types = self._enabled_message_types.get(component_type, set())
            for message_type in message_types:
                if message_type in enabled_message_types:
                    enabled_message_types.remove(message_type)
            if not enabled_message_types:
                del self._enabled_message_types[component_type]
            else:
                self._enabled_message_types[component_type] = enabled_message_types
