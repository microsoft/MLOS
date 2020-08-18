#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

class MlosTelemetryAggregator:
    """ An abstract class to be implemented by all classes that need to enable and consume mlos telemetry.

    """



    @property
    def requested_message_types(self):
        return self.callbacks.keys()

    @staticmethod
    def register_callback(component_type, message_type):
        """ Associates the message_type for which the decorated function should be called.

        :param message_type:
        :return:
        """
        def decorator(wrapped_function):
            wrapped_function.component_type = component_type
            wrapped_function.message_type = message_type
            return wrapped_function
        return decorator

    def __init__(self):
        """ Iterates over all methods defined in the subclass and finds ones that have been decorated.

        """

        # Callbacks is a dictionary where:
        # * key is the message type
        # * value is a List[Tuple[MlosSmartComponentSelector, callback]]
        self.callbacks = dict()

        for component_type, message_type, method in self._find_decorated_functions():
            existing_callbacks = self.callbacks.get((component_type, message_type), [])
            existing_callbacks.append(method)
            self.callbacks[(component_type, message_type)] = existing_callbacks

    def _find_decorated_functions(self):
        for attribute_name in dir(self):
            attribute = getattr(self, attribute_name)
            if callable(attribute):
                method = attribute
                if hasattr(method, 'message_type'):
                    message_type = method.message_type
                    component_type = method.component_type
                    yield component_type, message_type, method
