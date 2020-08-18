#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from contextlib import contextmanager
from threading import RLock

from . import mlos_globals


class MlosObject:
    """ The way for Smart Components to talk to Mlos.

    This object will:
    1. Contain a local copy of the configuration
    2. Contain a reference to a shared copy of the configuration
    3. Be connected to the communication channel

    """
    def __init__(self, smart_component_type, smart_component_runtime_attributes, default_config=None):
        """

        :param smart_component_type: class of the owning smart component. This is to look up the search space, etc.
        :param smart_component_runtime_attributes: attributes used to identify the component. If multiple components of the same type are present in
                the process, they can be filtered and grouped by some or all of their runtime attributes.
        """
        assert smart_component_type is not None and smart_component_runtime_attributes is not None

        self._reconfiguration_lock = RLock()
        self.owning_component_type = smart_component_type
        self.owning_component_runtime_attributes = smart_component_runtime_attributes

        self._current_config = default_config
        self._currently_enabled_message_types = set() # Can be efficiently represented as a bitmask if we are careful with codegen

    @contextmanager
    def reconfiguration_lock(self):
        """ Context manager to acquire the reconfiguration lock.

        We wrap the private _reconfiguration_lock with this context manager
        to allow for tracking/passing extra parameters, and changing implementation.

        :return:
        """
        with self._reconfiguration_lock:
            yield

    @property
    def config(self):
        with self.reconfiguration_lock():
            self._current_config = mlos_globals.mlos_global_context.get_current_config(self.owning_component_type)
            return self._current_config

    def enable_message_type(self, message_type):
        # NOTE: this can be an efficent compare-and-swap operation on the bitmask
        self._currently_enabled_message_types.add(message_type)

    def enable_message_types(self, message_types):
        for message_type in message_types:
            self._currently_enabled_message_types.add(message_type)

    def disable_message_type(self, message_type):
        if message_type in self._currently_enabled_message_types:
            self._currently_enabled_message_types.remove(message_type)

    def disable_message_types(self, message_types):
        for message_type in message_types:
            if message_type in self._currently_enabled_message_types:
                self._currently_enabled_message_types.remove(message_type)

    def disable_all_message_types(self):
        self._currently_enabled_message_types.clear()

    def register(self):
        mlos_globals.mlos_global_context.register_mlos_object(mlos_object=self)
        self.update_config()

    def unregister(self):
        mlos_globals.mlos_global_context.unregister_mlos_object(mlos_object=self)

    def update_config(self):
        with self.reconfiguration_lock():
            self._current_config = mlos_globals.mlos_global_context.get_current_config(self.owning_component_type)

    def is_message_type_enabled(self, message_type):
        return mlos_globals.mlos_global_context.is_message_type_enabled(self.owning_component_type, message_type)

    def send_telemetry_message(self, telemetry_message):
        if self.is_message_type_enabled(type(telemetry_message)):
            mlos_globals.mlos_global_context.send_telemetry_message(telemetry_message)

    # pylint: disable=no-self-use, unused-argument
    def get_runtime_decision_context(self, runtime_decision_type):
        """ Returns a decision context for a given decision type.

        :param runtime_decision_type:
        :return:
        """
        raise NotImplementedError

    def make_runtime_decision(self, runtime_decision_context):
        """ Makes a decision at runtime.

        :param runtime_decision_context:
        :return:
        """
        # TODO: hook it up to RL
        return runtime_decision_context.default_decision
