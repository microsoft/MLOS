#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from collections import namedtuple

# namedtuples are immutable, so they are pretty well suited for keeping track of all past
# configurations
Configuration = namedtuple(typename='Configuration', field_names=['component_type', 'values', 'id'])

class ConfigurationManager:
    """ Manages configuration updates for registered components.

    Background:
        Each SmartComponent contains a reference to an MlosObject and queries that object for
        configuration values.

        Occasionally, Mlos.Agent or another entity will update the configuration. The point of
        configuration manager is to ensure that that updated configuration is propagated to all
        relevant mlosObjects.

    The responsibility of ConfigurationManager is to allow the Mlos.Agent to suggest new configurations
    and to disseminate these configurations to smart components.

    Admittedly, the exact nature of these responsibilities remains nebulous.

    """

    def __init__(self, shared_config):

        self._shared_config = shared_config

        # A dictionary mapping component types with their historic configurations
        self._historic_configurations = dict()

        # A dictionary mapping component types with their search spaces
        self._parameter_search_spaces = dict()

    def add_allowed_component_type(self, component_type):
        if component_type in self._shared_config.allowed_component_types:
            raise RuntimeError(f"Component type {component_type.__name__} already allowed.")
        assert component_type.default_config in component_type.parameter_search_space
        self._parameter_search_spaces[component_type] = component_type.parameter_search_space
        self._shared_config.add_allowed_component(
            component_type=component_type,
            default_configuration=Configuration(
                component_type=component_type,
                values=component_type.default_config,
                id=0
            )
        )

    def set_configuration(self, component_type, new_config_values):
        # This will throw if the component is not available, or new_config is invalid
        assert new_config_values in self._parameter_search_spaces[component_type]
        old_configuration = self._shared_config.get_current_config(component_type)

        if component_type not in self._historic_configurations:
            self._historic_configurations[component_type] = dict()
        self._historic_configurations[component_type][old_configuration.id] = old_configuration

        new_configuration = Configuration(
            component_type=component_type,
            values=new_config_values,
            id=old_configuration.id + 1
        )

        self._shared_config.set_config(component_type, new_configuration)

    def get_configuration(self, component_type):
        current_configuration = self._shared_config.get_current_config(component_type)
        return current_configuration.values
