#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
class SmartComponentManager:
    """ Keeps track of smart components in the target process.

    The responsibilities of SmartComponentManager include:

    INTERNAL:

        1. Keeping track of all available smart components that could be instantiated in the target process.
        2. Keeping track of all smart components that are instantiated in the target process.
        3. Allowing smart components to register / unregister themselves.

    EXTERNAL:

        1. Exposing the list of potential components in this process.
        2. Exposing a list of instantiated components in the process.

    """
    def __init__(self):

        self._allowed_component_types = set()

        # Mapping component type to component type name
        self._allowed_component_type_names = dict()

        # The idea here is that we maintain a dictionary where:
        #   1. The key is a type of the smart component.
        #   2. The value is a dictionary where:
        #       1. The key is each component's (unique) runtime attributes
        #       2. The value is a reference to the mlos_object
        self._active_smart_components = dict() # TODO: consider a more sophisticated data structure

    def register_smart_component(self, component_type_name, component_runtime_attributes):
        if component_type_name not in self._allowed_component_type_names:
            raise RuntimeError(f"Component of type {component_type_name} cannot be registered as it is not on the list of allowed components.")

        component_type = self._allowed_component_type_names[component_type_name]
        existing_smart_components_of_this_type = self._active_smart_components.get(component_type, set())
        existing_smart_components_of_this_type.add(component_runtime_attributes)
        self._active_smart_components[component_type] = existing_smart_components_of_this_type

    def unregister_smart_component(self, component_type_name, component_runtime_attributes):
        component_type = self._allowed_component_type_names[component_type_name]

        if (component_type in self._active_smart_components) and (component_runtime_attributes in self._active_smart_components[component_type]):
            self._active_smart_components[component_type].remove(component_runtime_attributes)
            if not self._active_smart_components[component_type]:
                del self._active_smart_components[component_type]

    def enumerate_active_smart_components(self, component_selector=None):
        if component_selector is None:
            component_selector = lambda component_type, runtime_attributes: True
        for component_type, runtime_instances in self._active_smart_components.items():
            for runtime_attributes in runtime_instances:
                if component_selector(component_type, runtime_attributes):
                    yield component_type, runtime_attributes

    def add_allowed_component_type(self, component_type):
        if component_type in self._allowed_component_types:
            raise RuntimeError(f"Component type {component_type.__name__} already allowed.")
        self._allowed_component_types.add(component_type)
        self._allowed_component_type_names[component_type.__name__] = component_type

    def enumerate_allowed_component_types(self):
        for component_type in self._allowed_component_types:
            yield component_type
